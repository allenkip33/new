from flask import Flask, request, jsonify, make_response
from functools import wraps
import secrets
import requests

app = Flask(__name__)

inventory = [
    {
        "id": "1001",
        "name": "Wireless Mouse",
        "quantity": 50,
        "price": 29.99,
        "source": "manual"
    },
    {
        "id": "1002",
        "name": "Mechanical Keyboard",
        "quantity": 20,
        "price": 89.99,
        "source": "manual"
    }
]

next_id = 1003

SESSION_COOKIE = "inventory_session"
sessions = set()


def login_required(function):
    
    @wraps(function)
    def check_session(*args, **kwargs):
        session = request.cookies.get(SESSION_COOKIE)

        if session not in sessions:
            return jsonify({
                "error": "Please start a session first."
            }), 401

        return function(*args, **kwargs)

    return check_session


@app.route("/session", methods=["GET"])
def create_session():
    """Create a new session for the user."""

    session = secrets.token_urlsafe(32)
    sessions.add(session)

    response = make_response(
        jsonify({"message": "Session started"})
    )

    response.set_cookie(
        SESSION_COOKIE,
        session,
        max_age=60 * 60,
        httponly=True,
        samesite="Lax"
    )

    return response


def find_item(item_id):
    """Find an item using its ID."""

    for item in inventory:
        if item["id"] == str(item_id):
            return item

    return None


def get_next_id():
    """Generate the next available inventory ID."""

    global next_id

    while find_item(next_id):
        next_id += 1

    item_id = str(next_id)
    next_id += 1

    return item_id



@app.route("/inventory", methods=["GET"])
@login_required
def get_inventory():
    return jsonify(inventory), 200



@app.route("/inventory/<item_id>", methods=["GET"])
@login_required
def get_item(item_id):

    item = find_item(item_id)

    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def add_item():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Please send JSON data"
        }), 400

    if "name" not in data or "quantity" not in data or "price" not in data:
        return jsonify({
            "error": "Name, quantity and price are required"
        }), 400

    try:
        quantity = int(data["quantity"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "Quantity must be an integer"
        }), 400

    try:
        price = float(data["price"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "Price must be a number"
        }), 400


    source = data.get("source", "manual")

    if source != "manual" and data.get("id"):
        item_id = str(data["id"])

        if find_item(item_id):
            return jsonify({
                "error": "An item with this ID already exists"
            }), 400
    else:
        item_id = get_next_id()

    new_item = {
        "id": item_id,
        "name": data["name"],
        "quantity": quantity,
        "price": price,
        "source": source
    }

    inventory.append(new_item)

    return jsonify(new_item), 201


@app.route("/inventory/<item_id>", methods=["PATCH"])
def update_item(item_id):

    item = find_item(item_id)

    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        item["name"] = data["name"]

    if "quantity" in data:
        try:
            item["quantity"] = int(data["quantity"])
        except (ValueError, TypeError):
            return jsonify({
                "error": "Quantity must be an integer"
            }), 400

    if "price" in data:
        try:
            item["price"] = float(data["price"])
        except (ValueError, TypeError):
            return jsonify({
                "error": "Price must be a number"
            }), 400

    return jsonify(item), 200

@app.route("/inventory/<item_id>", methods=["DELETE"])
def delete_item(item_id):

    item = find_item(item_id)

    if not item:
        return jsonify({
            "error": "Item not found"
        }), 404

    inventory.remove(item)

    return jsonify({
        "message": "Item deleted successfully"
    }), 200


def search_open_food_facts(barcode):

    url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json"

    headers = {
        "User-Agent": "RetailInventorySystem/1.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=5
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data.get("product"):
            return None

        product = data["product"]

        return {
            "id": str(barcode),
            "name": product.get("product_name") or "Unknown Product",
            "quantity": 0,
            "price": 0.0,
            "source": "OpenFoodFacts API"
        }

    except (requests.RequestException, ValueError):
        return "error"


@app.route("/inventory/external/<barcode>", methods=["GET"])
def external_lookup(barcode):

    product = search_open_food_facts(barcode)

    if product == "error":
        return jsonify({
            "error": "Could not connect to the external service"
        }), 503

    if product is None:
        return jsonify({
            "found": False,
            "message": "Product was not found"
        }), 404

    return jsonify({
        "found": True,
        "data": product
    }), 200



if __name__ == "__main__":
    app.run(
        debug=True,
        port=5001
    )
