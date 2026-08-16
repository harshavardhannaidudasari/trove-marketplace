"""Populate the database with a realistic-looking demo catalog.

Run with: python -m app.seed.seed [--reset]

Images come from Picsum Photos (picsum.photos/seed/{id}/...) - real
photography, deterministic per product id, zero licensing risk. Never
scraped/copied from any real retailer.
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

TAXONOMY = {
    "Electronics": ["Headphones", "Laptops", "Smart Home", "Cameras", "Phone Accessories"],
    "Home & Kitchen": ["Cookware", "Small Appliances", "Furniture", "Bedding"],
    "Books": ["Fiction", "Non-Fiction", "Children's Books"],
    "Clothing": ["Men's", "Women's", "Kids'", "Shoes"],
    "Sports & Outdoors": ["Fitness Equipment", "Camping", "Cycling"],
    "Toys & Games": ["Board Games", "Building Sets", "Action Figures"],
    "Beauty": ["Skincare", "Haircare", "Fragrance"],
    "Grocery": ["Snacks", "Beverages", "Pantry Staples"],
    "Office": ["Desk Accessories", "Stationery", "Printers & Ink"],
    "Pet Supplies": ["Dog", "Cat", "Fish & Aquatics"],
}

PRICE_RANGES_CENTS = (999, 24999)
BRANDS = ["Nova", "Cascade", "Meridian", "Orbit", "Alderwood", "Brightside", "Fernway", "Kindle Peak", "Solace", "Vantage"]


def slugify(text: str) -> str:
    return "-".join(text.lower().replace("'", "").split())


def build_categories(db) -> list[Category]:
    leaf_categories = []
    for parent_name, children in TAXONOMY.items():
        parent = Category(name=parent_name, slug=slugify(parent_name))
        db.add(parent)
        db.flush()
        for child_name in children:
            child = Category(name=child_name, slug=slugify(f"{parent_name}-{child_name}"), parent_id=parent.id)
            db.add(child)
            leaf_categories.append(child)
        db.flush()
    return leaf_categories


def build_products(db, categories: list[Category], count: int) -> list[Product]:
    products = []
    for i in range(count):
        category = random.choice(categories)
        brand = random.choice(BRANDS)
        title = f"{brand} {fake.word().capitalize()} {category.name.rstrip('s')}"
        price = random.randint(*PRICE_RANGES_CENTS)
        has_discount = random.random() < 0.3
        product = Product(
            sku=f"SKU-{i:05d}",
            title=title,
            slug=f"{slugify(title)}-{i}",
            description=fake.paragraph(nb_sentences=5),
            price_cents=price,
            compare_at_price_cents=int(price * 1.25) if has_discount else None,
            category_id=category.id,
            brand=brand,
            stock_qty=random.randint(5, 200),
        )
        db.add(product)
        db.flush()
        for img_idx in range(3):
            db.add(
                ProductImage(
                    product_id=product.id,
                    url=f"https://picsum.photos/seed/trove-{i}-{img_idx}/700/700",
                    sort_order=img_idx,
                    alt_text=title,
                )
            )
        products.append(product)
    return products


def build_reviewer_pool(db, count: int = 12) -> list[User]:
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
        review_count = random.randint(0, 6)
        chosen_reviewers = random.sample(reviewers, k=min(review_count, len(reviewers)))
        ratings = []
        for reviewer in chosen_reviewers:
            rating = random.choices([3, 4, 5], weights=[1, 3, 5])[0]
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
        user_id=demo.id, line1="123 Market Street", city="Austin", state="TX", postal_code="78701", country="US", is_default=True
    )
    db.add(address)
    db.flush()

    picks = random.sample(products, k=3)
    subtotal = sum(p.price_cents for p in picks)
    tax = round(subtotal * 0.08)
    shipping = 0 if subtotal >= 5000 else 599
    order = Order(
        user_id=demo.id,
        status=OrderStatus.paid,
        subtotal_cents=subtotal,
        tax_cents=tax,
        shipping_cents=shipping,
        total_cents=subtotal + tax + shipping,
        shipping_address_id=address.id,
        stripe_payment_intent_id="pi_demo_seed_order",
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

    print(f"Demo login ready -> email: demo@trove.dev  password: DemoPass123!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables before seeding")
    parser.add_argument("--count", type=int, default=200, help="Number of products to generate")
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
        print(f"Seeded {len(categories)} categories, {len(products)} products, {len(reviewers)} reviewers.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
