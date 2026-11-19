from urllib.parse import quote
import requests

BASE_URL = "http://127.0.0.1:5000"


def send(method, path, data=None):
    try:
        response = requests.request(method, BASE_URL + path, json=data, timeout=10)
    except requests.exceptions.RequestException:
        print("Could not reach the API. Is the server running?")
        return None

    body = response.json()
    if response.status_code >= 400:
        print("Error:", body.get("error", "something went wrong"))
        return None
    return body


def show_item(item):
    print(f"{item['id']}. {item['product_name']} | {item['brands']} | KSh {item['price']} | stock: {item['stock']}")
    if item.get("ingredients_text"):
        print("   ingredients:", item["ingredients_text"])


def ask_number(prompt):
    while True:
        value = input(prompt)
        try:
            number = float(value)
        except ValueError:
            print("Please enter a number.")
            continue
        if number < 0:
            print("The number cannot be negative.")
            continue
        if number.is_integer():
            return int(number)
        return number


def ask_id():
    while True:
        value = input("Item id: ")
        if value.isdigit():
            return int(value)
        print("Please enter a whole number for the id.")


def view_all():
    items = send("GET", "/inventory")
    if items is None:
        return
    for item in items:
        show_item(item)


def view_one():
    item = send("GET", f"/inventory/{ask_id()}")
    if item:
        show_item(item)


def add_item():
    name = input("Product name: ").strip()
    if name == "":
        print("Product name cannot be empty.")
        return
    brand = input("Brand: ").strip()
    price = ask_number("Price: ")
    stock = ask_number("Stock: ")
    item = send("POST", "/inventory", {"product_name": name, "brands": brand, "price": price, "stock": stock})
    if item:
        print("Added:")
        show_item(item)


def update_item():
    item_id = ask_id()
    field = input("Update price or stock? ").strip().lower()
    if field not in ["price", "stock"]:
        print("Type price or stock.")
        return
    value = ask_number("New " + field + ": ")
    item = send("PATCH", f"/inventory/{item_id}", {field: value})
    if item:
        print("Updated:")
        show_item(item)


def delete_item():
    result = send("DELETE", f"/inventory/{ask_id()}")
    if result:
        print(result["message"])


def find_on_api():
    query = input("Barcode or product name: ").strip()
    if query == "":
        print("Please type something to search.")
        return
    details = send("GET", "/lookup/" + quote(query, safe=""))
    if details:
        print("Name:", details["product_name"])
        print("Brand:", details["brands"])
        print("Ingredients:", details["ingredients_text"])


def add_from_api():
    query = input("Barcode or product name: ").strip()
    if query == "":
        print("Please type something to search.")
        return
    price = ask_number("Price: ")
    stock = ask_number("Stock: ")
    item = send("POST", "/inventory/lookup", {"query": query, "price": price, "stock": stock})
    if item:
        print("Added from OpenFoodFacts:")
        show_item(item)


def main():
    options = {
        "1": view_all,
        "2": view_one,
        "3": add_item,
        "4": update_item,
        "5": delete_item,
        "6": find_on_api,
        "7": add_from_api,
    }
    while True:
        print()
        print("1. View all items")
        print("2. View one item")
        print("3. Add an item")
        print("4. Update price or stock")
        print("5. Delete an item")
        print("6. Find a product on OpenFoodFacts")
        print("7. Add a product from OpenFoodFacts")
        print("0. Quit")
        choice = input("Choose: ").strip()
        if choice == "0":
            break
        if choice in options:
            options[choice]()
        else:
            print("Invalid choice, pick a number from the menu.")


if __name__ == "__main__":
    main()
