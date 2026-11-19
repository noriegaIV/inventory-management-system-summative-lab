import copy
from unittest.mock import patch, Mock

import pytest
import requests

import app as inventory_app

original_inventory = copy.deepcopy(inventory_app.inventory)


@pytest.fixture
def client():
    inventory_app.inventory[:] = copy.deepcopy(original_inventory)
    return inventory_app.app.test_client()


def fake_response(data):
    response = Mock()
    response.json.return_value = data
    return response


# GET


def test_get_all_items(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.get_json()) == 5


def test_get_one_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Asali"


def test_get_missing_item(client):
    response = client.get("/inventory/99")
    assert response.status_code == 404


# POST


def test_add_item(client):
    new_item = {"product_name": "Kimyet", "brands": "Turukwei", "price": 300, "stock": 15}
    response = client.post("/inventory", json=new_item)
    assert response.status_code == 201
    assert response.get_json()["id"] == 6
    assert len(inventory_app.inventory) == 6


def test_add_item_missing_fields(client):
    response = client.post("/inventory", json={"product_name": "Kimyet"})
    assert response.status_code == 400


def test_add_item_bad_price(client):
    response = client.post("/inventory", json={"product_name": "Kimyet", "price": "free", "stock": 5})
    assert response.status_code == 400


# PATCH


def test_update_price(client):
    response = client.patch("/inventory/2", json={"price": 650})
    assert response.status_code == 200
    assert response.get_json()["price"] == 650
    assert inventory_app.find_item(2)["price"] == 650


def test_update_stock(client):
    response = client.patch("/inventory/3", json={"stock": 25})
    assert response.status_code == 200
    assert response.get_json()["stock"] == 25


def test_update_missing_item(client):
    response = client.patch("/inventory/99", json={"price": 100})
    assert response.status_code == 404


def test_update_bad_value(client):
    response = client.patch("/inventory/1", json={"stock": -5})
    assert response.status_code == 400


def test_update_empty_body(client):
    response = client.patch("/inventory/1", json={})
    assert response.status_code == 400


# DELETE


def test_delete_item(client):
    response = client.delete("/inventory/5")
    assert response.status_code == 200
    assert inventory_app.find_item(5) is None
    assert len(inventory_app.inventory) == 4


def test_delete_missing_item(client):
    response = client.delete("/inventory/99")
    assert response.status_code == 404


# external api, requests.get is mocked so no real internet call is made


def test_search_by_barcode():
    data = {"status": 1, "product": {"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "honey"}}
    with patch("app.requests.get", return_value=fake_response(data)) as mock_get:
        result = inventory_app.search_openfoodfacts("123456")
    assert "123456" in mock_get.call_args[0][0]
    assert result["product_name"] == "Honey"


def test_search_by_name():
    data = {"products": [{"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "honey"}]}
    with patch("app.requests.get", return_value=fake_response(data)) as mock_get:
        result = inventory_app.search_openfoodfacts("honey")
    assert mock_get.call_args[1]["params"]["search_terms"] == "honey"
    assert result["brands"] == "Bee Co"


def test_search_barcode_not_found():
    with patch("app.requests.get", return_value=fake_response({"status": 0})):
        assert inventory_app.search_openfoodfacts("000") is None


def test_search_name_not_found():
    with patch("app.requests.get", return_value=fake_response({"products": []})):
        assert inventory_app.search_openfoodfacts("zzzz") is None


def test_lookup_route(client):
    data = {"products": [{"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "honey"}]}
    with patch("app.requests.get", return_value=fake_response(data)):
        response = client.get("/lookup/honey")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Honey"


def test_lookup_route_not_found(client):
    with patch("app.requests.get", return_value=fake_response({"products": []})):
        response = client.get("/lookup/zzzz")
    assert response.status_code == 404


def test_lookup_route_api_down(client):
    with patch("app.requests.get", side_effect=requests.exceptions.ConnectionError):
        response = client.get("/lookup/honey")
    assert response.status_code == 502


def test_add_from_api(client):
    data = {"products": [{"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "honey"}]}
    with patch("app.requests.get", return_value=fake_response(data)):
        response = client.post("/inventory/lookup", json={"query": "honey", "price": 700, "stock": 8})
    assert response.status_code == 201
    assert response.get_json()["id"] == 6
    assert response.get_json()["ingredients_text"] == "honey"
    assert len(inventory_app.inventory) == 6


def test_add_from_api_missing_fields(client):
    response = client.post("/inventory/lookup", json={"query": "honey"})
    assert response.status_code == 400


def test_add_from_api_not_found(client):
    with patch("app.requests.get", return_value=fake_response({"products": []})):
        response = client.post("/inventory/lookup", json={"query": "zzzz", "price": 1, "stock": 1})
    assert response.status_code == 404
    assert len(inventory_app.inventory) == 5


def test_add_from_api_down(client):
    with patch("app.requests.get", side_effect=requests.exceptions.Timeout):
        response = client.post("/inventory/lookup", json={"query": "honey", "price": 1, "stock": 1})
    assert response.status_code == 502


def test_enrich_item(client):
    data = {"products": [{"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "pure honey"}]}
    with patch("app.requests.get", return_value=fake_response(data)):
        response = client.post("/inventory/1/enrich", json={"query": "honey"})
    assert response.status_code == 200
    assert inventory_app.find_item(1)["ingredients_text"] == "pure honey"
    assert inventory_app.find_item(1)["brands"] == "Turukwei"


def test_enrich_missing_item(client):
    response = client.post("/inventory/99/enrich", json={"query": "honey"})
    assert response.status_code == 404
