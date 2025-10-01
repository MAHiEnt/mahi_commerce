from flask import Flask, request, jsonify, g
from flask_cors import CORS
import stripe, json, os, sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from random import randint, choice
from waitress import serve

app = Flask(__name__)
CORS(app)
DATABASE = 'mahi_store.db'
stripe.api_key = os.environ.get('STRIPE_API_KEY')

SKU_CATEGORIES = {
    "kayak": [{"sku": "KAYAK-001", "label": "Solo Inflatable", "base_price": 299.99}, {"sku": "KAYAK-002", "label": "Tandem Rigid", "base_price": 499.00}],
    "camping": [{"sku": "CAMP-101", "label": "2-Person Tent", "base_price": 149.99}, {"sku": "CAMP-102", "label": "Sleeping Bag", "base_price": 89.50}],
    "survival": [{"sku": "SURV-201", "label": "Water Filter", "base_price": 39.99}, {"sku": "SURV-202", "label": "Emergency Kit", "base_price": 129.00}]
}

def get_db():
    db = getattr(g, '_database', None)
    if db is None: db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("CREATE TABLE IF NOT EXISTS bundles (id INTEGER PRIMARY KEY, bundle_id TEXT UNIQUE, category TEXT, status TEXT, items_json TEXT);")
        db.commit()
    print("Database initialized.")

@app.route('/generate_bundle', methods=['POST'])
def handle_generate_bundle():
    category = request.get_json().get('category')
    if not category or category not in SKU_CATEGORIES: return jsonify({"error": "Invalid category"}), 400
    items = [{"urgency_score": randint(1, 10), "clearance_flag": choice([True, False]), **item} for item in SKU_CATEGORIES[category]]
    bundle = {"bundle_id": f"MAHI-{uuid4().hex[:12]}", "category": category, "status": "pending", "items": items}
    db = get_db()
    db.execute('INSERT INTO bundles (bundle_id, category, status, items_json) VALUES (?, ?, ?, ?)', (bundle['bundle_id'], bundle['category'], bundle['status'], json.dumps(bundle['items'])))
    db.commit()
    return jsonify(bundle)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    bundle = request.get_json()
    line_items = []
    for item in bundle["items"]:
        final_price = int((item["base_price"] * (1.0 + (item["urgency_score"] / 20))) * (0.85 if item["clearance_flag"] else 1.0) * 100)
        line_items.append({"price_data": {"currency": "usd", "product_data": {"name": item["label"]}, "unit_amount": final_price}, "quantity": 1})
    session = stripe.checkout.Session.create(payment_method_types=["card"], line_items=line_items, mode="payment", success_url="https://floridamanadventures.com/success", cancel_url="https://floridamanadventures.com/cancel", metadata={'bundle_id': bundle.get('bundle_id')})
    return jsonify({"checkout_url": session.url})

@app.route('/')
def health_check(): return "MAHI Server is running."

if __name__ == '__main__':
    init_db()
    print("Starting MAHI server...")
    serve(app, host='0.0.0.0', port=5001)
