from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ------------------ DATA ------------------

# Products (your original 4 + 3 new)
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": True},
    {"id": 3, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": False},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
]

orders = []
feedback_list: List[dict] = []


# ------------------ MODELS (Day 2) ------------------

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)


# ------------------ BASIC ENDPOINTS (Day 1) ------------------

# Q1 — /products returns total: 7
@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# Q2 — Filter by category
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result, "total": len(result)}


# Q3 — In-stock products only
@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"] is True]
    return {"in_stock_products": available, "count": len(available)}


# Q5 — Search by keyword
@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    results = [p for p in products if keyword.lower() in p["name"].lower()]
    if not results:
        return {"message": "No products matched your search"}
    return {"keyword": keyword, "results": results, "total_matches": len(results)}


# Bonus — Cheapest & Most Expensive
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {"best_deal": cheapest, "premium_pick": expensive}


# Q4 — Store summary
@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_stock_count = len(products) - in_stock_count
    categories = list(set([p["category"] for p in products]))
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories,
    }


# ------------------ DAY 2 ENDPOINTS ------------------

# Q1 (Day 2) – /products/filter with min_price
@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_price: Optional[int] = Query(None, description="Minimum price"),
):
    result = products

    if category:
        result = [p for p in result if p["category"] == category]

    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]

    # NEW: min_price filter
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]

    return {
        "filters": {
            "category": category,
            "max_price": max_price,
            "min_price": min_price,
        },
        "products": result,
        "total": len(result),
    }


# Q2 (Day 2) – Product price by id
@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}


# Q3 (Day 2) – POST /feedback
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback_dict = data.dict()
    feedback_list.append(feedback_dict)
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback_dict,
        "total_feedback": len(feedback_list),
    }


# Q4 (Day 2) – Products summary
@app.get("/products/summary")
def product_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories,
    }


# Q5 (Day 2) – Bulk orders
@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock",
            })
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal,
            })

    bulk_order_record = {
        "order_id": len(orders) + 1,
        "type": "bulk",
        "company": order.company_name,
        "items": order.items,
        "grand_total": grand_total,
        "status": "pending",  # align with bonus flow
    }
    orders.append(bulk_order_record)

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total,
        "order_id": bulk_order_record["order_id"],
    }


# ------------------ BONUS (Order tracking) ------------------

# Simple single-order creation for demo
class SimpleOrder(BaseModel):
    product_id: int
    quantity: int


@app.post("/orders")
def create_order(order: SimpleOrder):
    product = next((p for p in products if p["id"] == order.product_id), None)
    if not product:
        return {"error": "Product not found"}

    status = "pending"  # bonus requirement
    order_record = {
        "order_id": len(orders) + 1,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": status,
    }
    orders.append(order_record)
    return {"message": "Order placed", "order": order_record}


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}
    return {"error": "Order not found"}


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}
    return {"error": "Order not found"}
