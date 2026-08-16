"""Populate the database with a large, realistic-looking demo catalog.

Run with: python -m app.seed.seed [--reset] [--count 900]

Images come from Picsum Photos (picsum.photos/seed/{id}/...) - real
photography, deterministic per product id, zero licensing risk. Product
names, brands, and copy are original / fictional - never scraped or
copied from any real retailer. Prices are in INR paise (price_cents).
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from faker import Faker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Address, CartItem, Category, Order, OrderItem, OrderStatus, Product, ProductImage, Review, User

fake = Faker()
Faker.seed(42)
random.seed(42)

# parent category -> (rupee price range, [ (subcategory, [product-type templates]) ])
TAXONOMY: dict[str, tuple[tuple[int, int], dict[str, list[str]]]] = {
    "Mobiles & Accessories": (
        (799, 149999),
        {
            "Smartphones": ["Smartphone (128GB)", "Smartphone (256GB, 5G)", "Budget Smartphone (64GB)"],
            "Phone Cases & Covers": ["Silicone Phone Case", "Rugged Armor Case", "Leather Flip Cover"],
            "Chargers & Cables": ["65W Fast Charger", "USB-C to USB-C Cable (1m)", "Wireless Charging Pad"],
            "Power Banks": ["10000mAh Power Bank", "20000mAh Fast-Charge Power Bank"],
            "Smartwatches": ["Fitness Smartwatch", "AMOLED Smartwatch with Calling"],
        },
    ),
    "Computers & Laptops": (
        (999, 199999),
        {
            "Laptops": ["14-inch Everyday Laptop", "15.6-inch Gaming Laptop", "Ultra-thin Business Laptop"],
            "Monitors": ["24-inch Full HD Monitor", "27-inch QHD IPS Monitor", "Curved Gaming Monitor"],
            "Keyboards & Mice": ["Wireless Mechanical Keyboard", "Ergonomic Wireless Mouse", "RGB Gaming Keyboard"],
            "Storage": ["1TB Portable SSD", "512GB NVMe Internal SSD", "32GB USB Flash Drive"],
            "Laptop Bags": ["15.6-inch Laptop Backpack", "Padded Laptop Sleeve"],
        },
    ),
    "TV, Audio & Cameras": (
        (499, 89999),
        {
            "Headphones": ["Wireless Bluetooth Headphones", "Over-Ear ANC Headphones", "True Wireless Earbuds", "Gaming Headset"],
            "Speakers": ["Portable Bluetooth Speaker", "Home Theatre Soundbar", "Smart Speaker with Voice Assistant"],
            "Televisions": ["43-inch 4K Smart TV", "55-inch 4K Smart TV", "32-inch HD Ready TV"],
            "Cameras": ["Mirrorless Camera with 18-55mm Lens", "Action Camera 4K", "Instant Print Camera"],
        },
    ),
    "Home & Kitchen": (
        (149, 49999),
        {
            "Cookware": ["Non-Stick Cookware Set", "Stainless Steel Kadai", "Cast Iron Skillet"],
            "Small Appliances": ["Air Fryer 4L", "Mixer Grinder 750W", "Electric Kettle 1.5L", "Induction Cooktop"],
            "Furniture": ["3-Seater Fabric Sofa", "Study Table with Drawer", "Bookshelf (5-Tier)", "Ergonomic Office Chair"],
            "Bedding": ["Cotton Bedsheet Set (Queen)", "Memory Foam Pillow", "Quilted Comforter"],
            "Home Decor": ["Wall Clock", "LED String Lights", "Decorative Wall Art Frame"],
        },
    ),
    "Fashion - Men": (
        (299, 7999),
        {
            "Men's T-Shirts": ["Cotton Crew-Neck T-Shirt", "Polo T-Shirt", "Graphic Print T-Shirt"],
            "Men's Shirts": ["Formal Cotton Shirt", "Checked Casual Shirt", "Linen Shirt"],
            "Men's Jeans & Trousers": ["Slim Fit Jeans", "Chino Trousers", "Track Pants"],
            "Men's Footwear": ["Running Shoes", "Leather Formal Shoes", "Casual Sneakers", "Sandals"],
        },
    ),
    "Fashion - Women": (
        (299, 8999),
        {
            "Women's Kurtas & Ethnic": ["Cotton A-Line Kurta", "Printed Anarkali Kurta", "Embroidered Saree"],
            "Women's Western Wear": ["Floral Maxi Dress", "High-Waist Jeans", "Casual Top"],
            "Women's Footwear": ["Block Heel Sandals", "Ballet Flats", "Running Shoes for Women"],
            "Handbags": ["Tote Handbag", "Sling Bag", "Laptop Tote for Women"],
        },
    ),
    "Fashion - Kids": (
        (199, 2999),
        {
            "Kids' Clothing": ["Kids Cotton T-Shirt Set", "Kids Party Dress", "Kids Winter Jacket"],
            "Kids' Footwear": ["Kids Sports Shoes", "Kids Sandals"],
        },
    ),
    "Books": (
        (99, 1999),
        {
            "Fiction": ["Mystery Thriller Novel", "Contemporary Fiction Novel", "Fantasy Adventure Novel"],
            "Non-Fiction": ["Self-Help & Personal Growth Book", "Popular Science Book", "Biography"],
            "Children's Books": ["Illustrated Picture Book", "Children's Story Collection"],
            "Academic & Reference": ["Competitive Exam Guide", "Programming Reference Book"],
        },
    ),
    "Beauty & Personal Care": (
        (99, 4999),
        {
            "Skincare": ["Vitamin C Face Serum", "Sunscreen SPF 50", "Hydrating Face Moisturizer", "Face Wash"],
            "Haircare": ["Anti-Dandruff Shampoo", "Argan Hair Oil", "Hair Straightener"],
            "Fragrance": ["Eau de Parfum for Men", "Eau de Parfum for Women", "Deodorant Body Spray"],
            "Grooming": ["Electric Trimmer", "Electric Shaver", "Manicure Kit"],
        },
    ),
    "Sports & Fitness": (
        (199, 24999),
        {
            "Fitness Equipment": ["Adjustable Dumbbell Set", "Yoga Mat (6mm)", "Resistance Bands Set", "Treadmill"],
            "Cycling": ["Hybrid Bicycle (26-inch)", "Cycling Helmet", "Bicycle Lock"],
            "Outdoor & Camping": ["2-Person Camping Tent", "Sleeping Bag", "Trekking Backpack 40L"],
            "Sportswear": ["Running Shoes (Unisex)", "Dry-Fit Sports T-Shirt"],
        },
    ),
    "Toys, Baby & Kids": (
        (149, 9999),
        {
            "Toys & Games": ["Building Blocks Set (200 pcs)", "Remote Control Car", "Board Game", "Soft Plush Toy"],
            "Baby Care": ["Baby Diaper Pack (Size M)", "Baby Stroller", "Baby Feeding Bottle Set"],
        },
    ),
    "Grocery & Gourmet": (
        (29, 1999),
        {
            "Snacks": ["Roasted Makhana Pack", "Multigrain Chips", "Protein Bar Pack (6)"],
            "Beverages": ["Instant Coffee Jar", "Green Tea Bags (100)", "Fruit Juice Pack (6x200ml)"],
            "Pantry Staples": ["Basmati Rice (5kg)", "Cold-Pressed Groundnut Oil (1L)", "Organic Honey (500g)"],
        },
    ),
    "Automotive": (
        (149, 29999),
        {
            "Car Accessories": ["Car Phone Mount", "Car Vacuum Cleaner", "Microfiber Car Cleaning Cloth Set", "Dashboard Camera"],
            "Bike Accessories": ["Bike Riding Gloves", "Motorcycle Helmet", "Bike Phone Holder"],
        },
    ),
    "Pet Supplies": (
        (99, 4999),
        {
            "Dog Supplies": ["Dry Dog Food (3kg)", "Dog Chew Toy", "Adjustable Dog Leash"],
            "Cat Supplies": ["Cat Litter (5L)", "Cat Scratching Post", "Dry Cat Food (1.5kg)"],
        },
    ),
    "Office Products": (
        (49, 14999),
        {
            "Stationery": ["Gel Pen Set (10 pcs)", "Spiral Notebook Pack", "Sticky Notes Set"],
            "Desk Accessories": ["Desk Organizer", "LED Desk Lamp", "Monitor Stand Riser"],
            "Printers & Ink": ["All-in-One Inkjet Printer", "Printer Ink Cartridge"],
        },
    ),
    "Health & Household": (
        (79, 6999),
        {
            "Health Devices": ["Digital Blood Pressure Monitor", "Digital Thermometer", "Pulse Oximeter"],
            "Household Supplies": ["Multi-Surface Cleaner (1L)", "Laundry Detergent (2kg)", "Air Purifier"],
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

    i = 0
    while len(products) < count:
        leaf, (lo, hi), templates = pool[i % len(pool)]
        i += 1
        brand = random.choice(BRANDS)
        template = random.choice(templates)
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
        for img_idx in range(4):
            db.add(
                ProductImage(
                    product_id=product.id,
                    url=f"https://picsum.photos/seed/trove-{i}-{img_idx}/900/900",
                    sort_order=img_idx,
                    alt_text=title,
                )
            )
        products.append(product)
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
