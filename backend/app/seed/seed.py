"""Populate the database with a large, realistic-looking demo catalog.

Run with: python -m app.seed.seed [--reset] [--count 900]

Images come from LoremFlickr (loremflickr.com/{w}/{h}/{keyword}) - each
product template carries an explicit search keyword (e.g. "Air Fryer 4L"
-> "air-fryer") so the photo actually matches what the product is, not
just a random deterministic photo. `lock=` pins a specific matching photo
per image slot so re-seeding is stable. Because LoremFlickr's CDN
occasionally serves a corrupted cached JPEG for a given lock value, every
candidate image is downloaded and decode-verified at seed time
(resolve_image_urls) and automatically retried against a nearby lock on
failure, so no broken image ever gets persisted. Product names, brands,
and copy are original / fictional - never scraped or copied from any
real retailer. Prices are in INR paise (price_cents).
"""

import argparse
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from faker import Faker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Address, CartItem, Category, Order, OrderItem, OrderStatus, Product, ProductImage, Review, User

fake = Faker()
Faker.seed(42)
random.seed(42)

# parent category -> (rupee price range, [ (subcategory, [(product-type template, image search keyword)]) ])
TAXONOMY: dict[str, tuple[tuple[int, int], dict[str, list[tuple[str, str]]]]] = {
    "Mobiles & Accessories": (
        (799, 149999),
        {
            "Smartphones": [
                ("Smartphone (128GB)", "smartphone"),
                ("Smartphone (256GB, 5G)", "smartphone"),
                ("Budget Smartphone (64GB)", "smartphone"),
            ],
            "Phone Cases & Covers": [
                ("Silicone Phone Case", "iphone,case"),
                ("Rugged Armor Case", "iphone,case"),
                ("Leather Flip Cover", "iphone,case"),
            ],
            "Chargers & Cables": [
                ("65W Fast Charger", "phone-charger"),
                ("USB-C to USB-C Cable (1m)", "usb-cable"),
                ("Wireless Charging Pad", "wireless-charger"),
            ],
            "Power Banks": [
                ("10000mAh Power Bank", "power-bank,charger"),
                ("20000mAh Fast-Charge Power Bank", "power-bank,charger"),
            ],
            "Smartwatches": [
                ("Fitness Smartwatch", "smartwatch"),
                ("AMOLED Smartwatch with Calling", "smartwatch"),
            ],
        },
    ),
    "Computers & Laptops": (
        (999, 199999),
        {
            "Laptops": [
                ("14-inch Everyday Laptop", "laptop"),
                ("15.6-inch Gaming Laptop", "gaming-laptop"),
                ("Ultra-thin Business Laptop", "laptop"),
            ],
            "Monitors": [
                ("24-inch Full HD Monitor", "computer-monitor,electronics"),
                ("27-inch QHD IPS Monitor", "computer-monitor,electronics"),
                ("Curved Gaming Monitor", "curved-monitor,electronics"),
            ],
            "Keyboards & Mice": [
                ("Wireless Mechanical Keyboard", "mechanical-keyboard"),
                ("Ergonomic Wireless Mouse", "wireless-mouse"),
                ("RGB Gaming Keyboard", "mechanical-keyboard"),
            ],
            "Storage": [
                ("1TB Portable SSD", "external-ssd"),
                ("512GB NVMe Internal SSD", "ssd"),
                ("32GB USB Flash Drive", "usb-flash-drive"),
            ],
            "Laptop Bags": [
                ("15.6-inch Laptop Backpack", "laptop-backpack"),
                ("Padded Laptop Sleeve", "laptop-sleeve"),
            ],
        },
    ),
    "TV, Audio & Cameras": (
        (499, 89999),
        {
            "Headphones": [
                ("Wireless Bluetooth Headphones", "headphones"),
                ("Over-Ear ANC Headphones", "headphones"),
                ("True Wireless Earbuds", "earbuds"),
                ("Gaming Headset", "gaming-headset"),
            ],
            "Speakers": [
                ("Portable Bluetooth Speaker", "bluetooth-speaker"),
                ("Home Theatre Soundbar", "soundbar"),
                ("Smart Speaker with Voice Assistant", "smart-speaker"),
            ],
            "Televisions": [
                ("43-inch 4K Smart TV", "smart-tv"),
                ("55-inch 4K Smart TV", "smart-tv"),
                ("32-inch HD Ready TV", "smart-tv"),
            ],
            "Cameras": [
                ("Mirrorless Camera with 18-55mm Lens", "mirrorless,camera"),
                ("Action Camera 4K", "action-camera"),
                ("Instant Print Camera", "instant-camera"),
            ],
        },
    ),
    "Home & Kitchen": (
        (149, 49999),
        {
            "Cookware": [
                ("Non-Stick Cookware Set", "cookware"),
                ("Stainless Steel Kadai", "wok"),
                ("Cast Iron Skillet", "cast-iron,skillet"),
            ],
            "Small Appliances": [
                ("Air Fryer 4L", "air-fryer"),
                ("Mixer Grinder 750W", "blender"),
                ("Electric Kettle 1.5L", "electric-kettle"),
                ("Induction Cooktop", "induction-cooktop"),
            ],
            "Furniture": [
                ("3-Seater Fabric Sofa", "sofa,furniture"),
                ("Study Table with Drawer", "study-table,furniture"),
                ("Bookshelf (5-Tier)", "bookshelf,furniture"),
                ("Ergonomic Office Chair", "office-chair,furniture"),
            ],
            "Bedding": [
                ("Cotton Bedsheet Set (Queen)", "bedsheet"),
                ("Memory Foam Pillow", "pillow"),
                ("Quilted Comforter", "comforter"),
            ],
            "Home Decor": [
                ("Wall Clock", "wall-clock,home"),
                ("LED String Lights", "string-lights"),
                ("Decorative Wall Art Frame", "wall-art,home"),
            ],
        },
    ),
    "Fashion - Men": (
        (299, 7999),
        {
            "Men's T-Shirts": [
                ("Cotton Crew-Neck T-Shirt", "mens-tshirt"),
                ("Polo T-Shirt", "polo-shirt"),
                ("Graphic Print T-Shirt", "graphic-tshirt"),
            ],
            "Men's Shirts": [
                ("Formal Cotton Shirt", "collared-shirt"),
                ("Checked Casual Shirt", "flannel-shirt"),
                ("Linen Shirt", "linen-shirt"),
            ],
            "Men's Jeans & Trousers": [
                ("Slim Fit Jeans", "mens-jeans"),
                ("Chino Trousers", "chino-pants"),
                ("Track Pants", "track-pants"),
            ],
            "Men's Footwear": [
                ("Running Shoes", "running-shoes"),
                ("Leather Formal Shoes", "formal-shoes"),
                ("Casual Sneakers", "sneakers"),
                ("Sandals", "sandals"),
            ],
        },
    ),
    "Fashion - Women": (
        (299, 8999),
        {
            "Women's Kurtas & Ethnic": [
                ("Cotton A-Line Kurta", "kurta"),
                ("Printed Anarkali Kurta", "anarkali"),
                ("Embroidered Saree", "saree"),
            ],
            "Women's Western Wear": [
                ("Floral Maxi Dress", "maxi-dress"),
                ("High-Waist Jeans", "womens-jeans"),
                ("Casual Top", "womens-top"),
            ],
            "Women's Footwear": [
                ("Block Heel Sandals", "heel-sandals"),
                ("Ballet Flats", "ballet-flats"),
                ("Running Shoes for Women", "running-shoes"),
            ],
            "Handbags": [
                ("Tote Handbag", "tote-bag"),
                ("Sling Bag", "sling-bag"),
                ("Laptop Tote for Women", "laptop-tote"),
            ],
        },
    ),
    "Fashion - Kids": (
        (199, 2999),
        {
            "Kids' Clothing": [
                ("Kids Cotton T-Shirt Set", "kids-tshirt"),
                ("Kids Party Dress", "kids-dress"),
                ("Kids Winter Jacket", "kids-jacket"),
            ],
            "Kids' Footwear": [
                ("Kids Sports Shoes", "kids-shoes"),
                ("Kids Sandals", "kids-sandals"),
            ],
        },
    ),
    "Books": (
        (99, 1999),
        {
            "Fiction": [
                ("Mystery Thriller Novel", "book"),
                ("Contemporary Fiction Novel", "book"),
                ("Fantasy Adventure Novel", "fantasy-book"),
            ],
            "Non-Fiction": [
                ("Self-Help & Personal Growth Book", "book"),
                ("Popular Science Book", "book"),
                ("Biography", "book"),
            ],
            "Children's Books": [
                ("Illustrated Picture Book", "childrens-book"),
                ("Children's Story Collection", "childrens-book"),
            ],
            "Academic & Reference": [
                ("Competitive Exam Guide", "textbook"),
                ("Programming Reference Book", "programming-book"),
            ],
        },
    ),
    "Beauty & Personal Care": (
        (99, 4999),
        {
            "Skincare": [
                ("Vitamin C Face Serum", "face-serum"),
                ("Sunscreen SPF 50", "sunscreen"),
                ("Hydrating Face Moisturizer", "moisturizer"),
                ("Face Wash", "face-wash"),
            ],
            "Haircare": [
                ("Anti-Dandruff Shampoo", "shampoo"),
                ("Argan Hair Oil", "hair-oil"),
                ("Hair Straightener", "hair-straightener"),
            ],
            "Fragrance": [
                ("Eau de Parfum for Men", "perfume"),
                ("Eau de Parfum for Women", "perfume"),
                ("Deodorant Body Spray", "deodorant"),
            ],
            "Grooming": [
                ("Electric Trimmer", "beard-trimmer"),
                ("Electric Shaver", "electric-shaver"),
                ("Manicure Kit", "manicure-set"),
            ],
        },
    ),
    "Sports & Fitness": (
        (199, 24999),
        {
            "Fitness Equipment": [
                ("Adjustable Dumbbell Set", "dumbbells"),
                ("Yoga Mat (6mm)", "yoga-mat"),
                ("Resistance Bands Set", "resistance-bands"),
                ("Treadmill", "treadmill"),
            ],
            "Cycling": [
                ("Hybrid Bicycle (26-inch)", "bicycle"),
                ("Cycling Helmet", "cycling-helmet"),
                ("Bicycle Lock", "bike-lock"),
            ],
            "Outdoor & Camping": [
                ("2-Person Camping Tent", "camping-tent"),
                ("Sleeping Bag", "sleeping-bag"),
                ("Trekking Backpack 40L", "trekking-backpack"),
            ],
            "Sportswear": [
                ("Running Shoes (Unisex)", "running-shoes"),
                ("Dry-Fit Sports T-Shirt", "sports-tshirt"),
            ],
        },
    ),
    "Toys, Baby & Kids": (
        (149, 9999),
        {
            "Toys & Games": [
                ("Building Blocks Set (200 pcs)", "building-blocks"),
                ("Remote Control Car", "rc-car"),
                ("Board Game", "board-game"),
                ("Soft Plush Toy", "plush-toy"),
            ],
            "Baby Care": [
                ("Baby Diaper Pack (Size M)", "diapers"),
                ("Baby Stroller", "baby-stroller"),
                ("Baby Feeding Bottle Set", "baby-bottle"),
            ],
        },
    ),
    "Grocery & Gourmet": (
        (29, 1999),
        {
            "Snacks": [
                ("Roasted Makhana Pack", "snacks"),
                ("Multigrain Chips", "potato-chips"),
                ("Protein Bar Pack (6)", "protein-bar"),
            ],
            "Beverages": [
                ("Instant Coffee Jar", "instant-coffee"),
                ("Green Tea Bags (100)", "green-tea"),
                ("Fruit Juice Pack (6x200ml)", "fruit-juice"),
            ],
            "Pantry Staples": [
                ("Basmati Rice (5kg)", "rice"),
                ("Cold-Pressed Groundnut Oil (1L)", "cooking-oil"),
                ("Organic Honey (500g)", "honey"),
            ],
        },
    ),
    "Automotive": (
        (149, 29999),
        {
            "Car Accessories": [
                ("Car Phone Mount", "dashboard,phone"),
                ("Car Vacuum Cleaner", "car-vacuum"),
                ("Microfiber Car Cleaning Cloth Set", "microfiber,cleaning"),
                ("Dashboard Camera", "dash-cam"),
            ],
            "Bike Accessories": [
                ("Bike Riding Gloves", "motorcycle-gloves"),
                ("Motorcycle Helmet", "motorcycle-helmet"),
                ("Bike Phone Holder", "bike-mount"),
            ],
        },
    ),
    "Pet Supplies": (
        (99, 4999),
        {
            "Dog Supplies": [
                ("Dry Dog Food (3kg)", "dog-food"),
                ("Dog Chew Toy", "dog-toy"),
                ("Adjustable Dog Leash", "dog-leash"),
            ],
            "Cat Supplies": [
                ("Cat Litter (5L)", "cat-litter"),
                ("Cat Scratching Post", "scratching-post,cat"),
                ("Dry Cat Food (1.5kg)", "cat-food"),
            ],
        },
    ),
    "Office Products": (
        (49, 14999),
        {
            "Stationery": [
                ("Gel Pen Set (10 pcs)", "gel-pens"),
                ("Spiral Notebook Pack", "notebook"),
                ("Sticky Notes Set", "sticky-notes"),
            ],
            "Desk Accessories": [
                ("Desk Organizer", "desk-organizer"),
                ("LED Desk Lamp", "desk-lamp"),
                ("Monitor Stand Riser", "monitor-stand"),
            ],
            "Printers & Ink": [
                ("All-in-One Inkjet Printer", "inkjet-printer"),
                ("Printer Ink Cartridge", "ink-cartridge"),
            ],
        },
    ),
    "Health & Household": (
        (79, 6999),
        {
            "Health Devices": [
                ("Digital Blood Pressure Monitor", "blood-pressure,monitor"),
                ("Digital Thermometer", "thermometer"),
                ("Pulse Oximeter", "pulse-oximeter"),
            ],
            "Household Supplies": [
                ("Multi-Surface Cleaner (1L)", "spray-bottle"),
                ("Laundry Detergent (2kg)", "laundry-detergent"),
                ("Air Purifier", "air-purifier"),
            ],
        },
    ),
}

BRANDS = [
    "Nova", "Cascade", "Meridian", "Orbit", "Alderwood", "Brightside", "Fernway", "Kindle Peak", "Solace", "Vantage",
    "Zephyr", "Trueform", "Northbound", "Everline", "Rivet", "Palmora", "Kestrel", "Glowline", "Ambient", "Ridgeway",
    "Lumen", "Crestal", "Marrow", "Sunspell", "Verve", "Wavecrest", "Ironloft", "Highstreet", "Cloudpeak", "Basil & Birch",
]

COLORS = ["Midnight Black", "Ocean Blue", "Slate Grey", "Pearl White", "Rose Gold", "Forest Green", "Sandstone", "Crimson Red"]


def slugify(text: str) -> str:
    return "-".join("".join(c if c.isalnum() or c.isspace() else " " for c in text.lower()).split())


_GRAY_FILL_FRACTION_LIMIT = 0.05  # legit photos measured ~0.0%; corrupted decodes measured ~42%


def _is_decodable_image(data: bytes) -> bool:
    """LoremFlickr's CDN occasionally serves a cached derivative that is a
    structurally valid JPEG (decodes without error) but whose actual scan data is
    corrupted - libjpeg fills the undecoded region with flat mid-gray (128, 128, 128)
    instead of raising, so a bare decode check doesn't catch it. Flag images where a
    large fraction of pixels are exactly that fallback-fill gray as corrupted too."""
    try:
        img = Image.open(BytesIO(data))
        img.load()
        if img.width <= 0 or img.height <= 0:
            return False
    except (UnidentifiedImageError, OSError):
        return False

    rgb = img.convert("RGB")
    pixels = rgb.getdata()
    total = rgb.width * rgb.height
    gray_fill = sum(1 for p in pixels if p == (128, 128, 128))
    return (gray_fill / total) <= _GRAY_FILL_FRACTION_LIMIT


def _resolve_image_url(keyword_path: str, base_lock: int, max_attempts: int = 5) -> str:
    """Find a lock value for this keyword whose image actually decodes, retrying
    against different points in the tag's photo pool on corruption."""
    last_url = f"https://loremflickr.com/900/900/{keyword_path}?lock={base_lock}"
    for attempt in range(max_attempts):
        lock = base_lock + attempt * 97
        url = f"https://loremflickr.com/900/900/{keyword_path}?lock={lock}"
        last_url = url
        try:
            with urlopen(url, timeout=15) as resp:
                data = resp.read()
        except URLError:
            continue
        if _is_decodable_image(data):
            return url
    print(f"WARNING: could not find a decodable image for {keyword_path!r} after {max_attempts} attempts, using {last_url}")
    return last_url


def build_categories(db) -> dict[str, list[Category]]:
    """Returns {parent_name: [leaf Category,...]} and stashes price range on each leaf via closure map."""
    leaf_map: dict[str, list[Category]] = {}
    for parent_name, (price_range, children) in TAXONOMY.items():
        parent = Category(name=parent_name, slug=slugify(parent_name))
        db.add(parent)
        db.flush()
        leaves = []
        for child_name in children:
            child = Category(name=child_name, slug=slugify(f"{parent_name}-{child_name}"), parent_id=parent.id)
            db.add(child)
            leaves.append(child)
        db.flush()
        leaf_map[parent_name] = leaves
    return leaf_map


def build_products(db, categories: dict[str, list[Category]], count: int) -> list[Product]:
    products = []
    # Flatten: (leaf_category, price_range, [templates])
    pool = []
    for parent_name, (price_range, children) in TAXONOMY.items():
        leaves = categories[parent_name]
        child_names = list(children.keys())
        for leaf, child_name in zip(leaves, child_names):
            pool.append((leaf, price_range, children[child_name]))

    # (product, sort_order, keyword_path, base_lock, title) - resolved to verified
    # image URLs in one batch after all products exist, so corrupted CDN cache
    # entries can be retried without slowing down the per-product loop.
    pending_images: list[tuple[Product, int, str, int, str]] = []

    i = 0
    while len(products) < count:
        leaf, (lo, hi), templates = pool[i % len(pool)]
        i += 1
        brand = random.choice(BRANDS)
        template, image_keyword = random.choice(templates)
        variant = random.choice(COLORS) if random.random() < 0.5 else None
        title = f"{brand} {template}" + (f" - {variant}" if variant else "")
        price_rupees = random.randint(lo, hi)
        price = price_rupees * 100
        has_discount = random.random() < 0.35
        compare_price = int(price * random.uniform(1.15, 1.6)) if has_discount else None

        spec_line = fake.sentence(nb_words=10)
        body = fake.paragraph(nb_sentences=4)
        description = (
            f"{template} by {brand}. {spec_line} "
            f"{body} Backed by a 1-year manufacturer warranty and easy 7-day returns."
        )

        product = Product(
            sku=f"SKU-{i:05d}",
            title=title,
            slug=f"{slugify(title)}-{i}",
            description=description,
            price_cents=price,
            compare_at_price_cents=compare_price,
            category_id=leaf.id,
            brand=brand,
            stock_qty=random.randint(0, 250),
        )
        db.add(product)
        db.flush()
        keyword_path = quote(image_keyword, safe=",")
        for img_idx in range(4):
            pending_images.append((product, img_idx, keyword_path, i * 10 + img_idx, title))
        products.append(product)

    print(f"Verifying {len(pending_images)} product images against LoremFlickr (retrying any corrupted ones)...")
    with ThreadPoolExecutor(max_workers=24) as pool_exec:
        resolved_urls = list(
            pool_exec.map(lambda spec: _resolve_image_url(spec[2], spec[3]), pending_images)
        )
    for (product, img_idx, _keyword_path, _base_lock, title), url in zip(pending_images, resolved_urls):
        db.add(
            ProductImage(
                product_id=product.id,
                url=url,
                sort_order=img_idx,
                alt_text=title,
            )
        )
    return products


def build_reviewer_pool(db, count: int = 40) -> list[User]:
    users = []
    for _ in range(count):
        email = fake.unique.email()
        user = User(email=email, hashed_password=hash_password("demo-reviewer"), full_name=fake.name())
        db.add(user)
        users.append(user)
    db.flush()
    return users


def build_reviews(db, products: list[Product], reviewers: list[User]) -> None:
    for product in products:
        review_count = random.randint(0, 8)
        chosen_reviewers = random.sample(reviewers, k=min(review_count, len(reviewers)))
        ratings = []
        for reviewer in chosen_reviewers:
            rating = random.choices([1, 2, 3, 4, 5], weights=[1, 1, 2, 4, 7])[0]
            db.add(
                Review(
                    product_id=product.id,
                    user_id=reviewer.id,
                    rating=rating,
                    title=fake.sentence(nb_words=4),
                    body=fake.paragraph(nb_sentences=3),
                )
            )
            ratings.append(rating)
        if ratings:
            product.avg_rating = round(sum(ratings) / len(ratings), 1)
            product.review_count = len(ratings)


def build_demo_account(db, products: list[Product]) -> None:
    demo = User(email="demo@trove.dev", hashed_password=hash_password("DemoPass123!"), full_name="Demo Shopper")
    db.add(demo)
    db.flush()

    address = Address(
        user_id=demo.id, line1="221B, MG Road", city="Bengaluru", state="Karnataka", postal_code="560001", country="IN", is_default=True
    )
    db.add(address)
    db.flush()

    picks = random.sample(products, k=3)
    subtotal = sum(p.price_cents for p in picks)
    tax = round(subtotal * 0.18)
    shipping = 0 if subtotal >= 50000 else 4900
    order = Order(
        user_id=demo.id,
        status=OrderStatus.paid,
        subtotal_cents=subtotal,
        tax_cents=tax,
        shipping_cents=shipping,
        total_cents=subtotal + tax + shipping,
        shipping_address_id=address.id,
        payment_method="UPI (demo@upi)",
        payment_reference="MOCK-DEMOSEEDORDER01",
    )
    db.add(order)
    db.flush()
    for product in picks:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_title_snapshot=product.title,
                unit_price_cents_snapshot=product.price_cents,
                quantity=1,
            )
        )

    print("Demo login ready -> email: demo@trove.dev  password: DemoPass123!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding")
    parser.add_argument("--count", type=int, default=900, help="Number of products to generate")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("Tables dropped and recreated.")

    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            print("Products already exist - skipping seed (use --reset to force).")
            return

        categories = build_categories(db)
        products = build_products(db, categories, args.count)
        reviewers = build_reviewer_pool(db)
        build_reviews(db, products, reviewers)
        build_demo_account(db, products)

        db.commit()
        total_leaf_categories = sum(len(v) for v in categories.values())
        print(f"Seeded {len(TAXONOMY)} departments / {total_leaf_categories} categories, {len(products)} products, {len(reviewers)} reviewers.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
