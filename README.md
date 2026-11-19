# Inventory Management System

A small Flask REST API for managing inventory for Turukwei, a seller of traditional products. It also has a command line tool to use the API and can fetch extra product details from the OpenFoodFacts API.

The data is stored in a Python list in `app.py`, so it resets whenever the server restarts.

## Files

- `app.py` - Flask API and the starting inventory
- `cli.py` - command line tool
- `test_app.py` - tests for the API routes and OpenFoodFacts calls
- `test_cli.py` - tests for the CLI
- `requirements.txt` - packages needed

## Setup

```
git clone https://github.com/noriegaIV/inventory-management-system-summative-lab.git
cd inventory-management-system-summative-lab
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

Start the API (debug mode is on):

```
python app.py
```

The API runs at http://127.0.0.1:5000. In a second terminal, start the CLI:

```
python cli.py
```

## API endpoints

| Method | Endpoint | What it does |
| --- | --- | --- |
| GET | `/inventory` | get all items |
| GET | `/inventory/<id>` | get one item |
| POST | `/inventory` | add an item (`product_name`, `price`, `stock`, optional `brands`) |
| PATCH | `/inventory/<id>` | update an item (any of `product_name`, `brands`, `price`, `stock`, `ingredients_text`) |
| DELETE | `/inventory/<id>` | delete an item |
| GET | `/lookup/<barcode or name>` | find a product on OpenFoodFacts |
| POST | `/inventory/lookup` | find a product on OpenFoodFacts and add it (`query`, `price`, `stock`) |
| POST | `/inventory/<id>/enrich` | fill an item's ingredients from OpenFoodFacts (optional `query`, defaults to the item name) |

Errors come back as JSON like `{"error": "Item not found"}` with a 400, 404 or 502 status. 502 means OpenFoodFacts could not be reached.

Example with curl:

```
curl http://127.0.0.1:5000/inventory/1
curl -X POST http://127.0.0.1:5000/inventory -H "Content-Type: application/json" -d '{"product_name": "Kimyet", "brands": "Turukwei", "price": 300, "stock": 15}'
curl -X PATCH http://127.0.0.1:5000/inventory/1 -H "Content-Type: application/json" -d '{"price": 1100}'
curl -X DELETE http://127.0.0.1:5000/inventory/1
```

## CLI commands

Run `python cli.py` and pick a number from the menu:

```
1. View all items
2. View one item
3. Add an item
4. Update price or stock
5. Delete an item
6. Find a product on OpenFoodFacts
7. Add a product from OpenFoodFacts
0. Quit
```

Example, updating a price:

```
Choose: 4
Item id: 2
Update price or stock? price
New price: 650
Updated:
2. Seshiante | Turukwei | KSh 650 | stock: 30
```

The CLI checks the input (ids and numbers must be valid) and prints a message if the API returns an error or the server is not running.

## Tests

```
pytest
```

The tests mock the OpenFoodFacts calls, so they do not need internet. The API was also debugged with Flask debug mode and curl.

## Starting inventory

| id | product | price (KSh) | stock |
| --- | --- | --- | --- |
| 1 | Asali | 1000 | 20 |
| 2 | Seshiante | 500 | 30 |
| 3 | Kipketen | 200 | 10 |
| 4 | Ngengte | 900 | 60 |
| 5 | Mursik | 100 | 50 |

All items use the brand Turukwei.
