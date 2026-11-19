from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# temporary storage, it resets every time the server restarts
inventory = [
    {"id": 1, "product_name": "Asali", "brands": "Turukwei", "price": 1000, "stock": 20, "ingredients_text": ""},
    {"id": 2, "product_name": "Seshiante", "brands": "Turukwei", "price": 500, "stock": 30, "ingredients_text": ""},
    {"id": 3, "product_name": "Kipketen", "brands": "Turukwei", "price": 200, "stock": 10, "ingredients_text": ""},
    {"id": 4, "product_name": "Ngengte", "brands": "Turukwei", "price": 900, "stock": 60, "ingredients_text": ""},
    {"id": 5, "product_name": "Mursik", "brands": "Turukwei", "price": 100, "stock": 50, "ingredients_text": ""},
]


def find_item(item_id):
    for item in inventory:
        if item["id"] == item_id:
            return item
    return None


def next_id():
    if len(inventory) == 0:
        return 1
    return max(item["id"] for item in inventory) + 1


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def search_openfoodfacts(query):
    # all digits means it is a barcode, otherwise search by name
    if query.isdigit():
        url = f"https://world.openfoodfacts.org/api/v0/product/{query}.json"
        data = requests.get(url, timeout=10).json()
        if data.get("status") != 1:
            return None
        product = data["product"]
    else:
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 1,
        }
        products = requests.get(url, params=params, timeout=10).json().get("products", [])
        if len(products) == 0:
            return None
        product = products[0]

    return {
        "product_name": product.get("product_name", ""),
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
    }


@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(inventory), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def add_item():
    data = request.get_json(silent=True)
    if not data or "product_name" not in data or "price" not in data or "stock" not in data:
        return jsonify({"error": "product_name, price and stock are required"}), 400
    if not valid_number(data["price"]) or not valid_number(data["stock"]):
        return jsonify({"error": "price and stock must be numbers that are not negative"}), 400

    new_item = {
        "id": next_id(),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "price": data["price"],
        "stock": data["stock"],
        "ingredients_text": data.get("ingredients_text", ""),
    }
    inventory.append(new_item)
    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Send the fields you want to change"}), 400

    for key in ["product_name", "brands", "price", "stock", "ingredients_text"]:
        if key in data:
            if key in ["price", "stock"] and not valid_number(data[key]):
                return jsonify({"error": key + " must be a number that is not negative"}), 400
            item[key] = data[key]
    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    inventory.remove(item)
    return jsonify({"message": "Item deleted"}), 200


# helper routes for the external api


@app.route("/lookup/<query>", methods=["GET"])
def lookup(query):
    try:
        details = search_openfoodfacts(query)
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    if details is None:
        return jsonify({"error": "Product not found on OpenFoodFacts"}), 404
    return jsonify(details), 200


@app.route("/inventory/lookup", methods=["POST"])
def add_from_api():
    data = request.get_json(silent=True)
    if not data or "query" not in data or "price" not in data or "stock" not in data:
        return jsonify({"error": "query, price and stock are required"}), 400
    if not valid_number(data["price"]) or not valid_number(data["stock"]):
        return jsonify({"error": "price and stock must be numbers that are not negative"}), 400

    try:
        details = search_openfoodfacts(data["query"])
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    if details is None:
        return jsonify({"error": "Product not found on OpenFoodFacts"}), 404

    new_item = {
        "id": next_id(),
        "product_name": details["product_name"],
        "brands": details["brands"],
        "price": data["price"],
        "stock": data["stock"],
        "ingredients_text": details["ingredients_text"],
    }
    inventory.append(new_item)
    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>/enrich", methods=["POST"])
def enrich_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    data = request.get_json(silent=True) or {}
    query = data.get("query", item["product_name"])

    try:
        details = search_openfoodfacts(query)
    except requests.exceptions.RequestException:
        return jsonify({"error": "Could not reach OpenFoodFacts"}), 502
    if details is None:
        return jsonify({"error": "Product not found on OpenFoodFacts"}), 404

    item["ingredients_text"] = details["ingredients_text"]
    return jsonify(item), 200


if __name__ == "__main__":
    app.run(debug=True)
