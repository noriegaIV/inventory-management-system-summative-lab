from unittest.mock import patch, Mock

import requests

import cli


def fake_response(data, status=200):
    response = Mock()
    response.status_code = status
    response.json.return_value = data
    return response


item = {"id": 1, "product_name": "Asali", "brands": "Turukwei", "price": 1000, "stock": 20, "ingredients_text": ""}


def test_send_returns_data():
    with patch("cli.requests.request", return_value=fake_response([item])):
        assert cli.send("GET", "/inventory") == [item]


def test_send_prints_api_error(capsys):
    with patch("cli.requests.request", return_value=fake_response({"error": "Item not found"}, 404)):
        assert cli.send("GET", "/inventory/99") is None
    assert "Item not found" in capsys.readouterr().out


def test_send_server_down(capsys):
    with patch("cli.requests.request", side_effect=requests.exceptions.ConnectionError):
        assert cli.send("GET", "/inventory") is None
    assert "Could not reach the API" in capsys.readouterr().out


def test_view_all(capsys):
    with patch("cli.requests.request", return_value=fake_response([item])):
        cli.view_all()
    assert "Asali" in capsys.readouterr().out


def test_view_all_server_down(capsys):
    with patch("cli.requests.request", side_effect=requests.exceptions.ConnectionError):
        cli.view_all()
    assert "Could not reach the API" in capsys.readouterr().out


def test_view_one(capsys):
    with patch("builtins.input", return_value="1"):
        with patch("cli.requests.request", return_value=fake_response(item)) as mock_request:
            cli.view_one()
    assert mock_request.call_args[0][1].endswith("/inventory/1")
    assert "Asali" in capsys.readouterr().out


def test_ask_id_retries_on_bad_input(capsys):
    with patch("builtins.input", side_effect=["abc", "-2", "3"]):
        assert cli.ask_id() == 3
    assert "whole number" in capsys.readouterr().out


def test_ask_number_retries_on_bad_input(capsys):
    with patch("builtins.input", side_effect=["abc", "-4", "250"]):
        assert cli.ask_number("Price: ") == 250
    output = capsys.readouterr().out
    assert "Please enter a number" in output
    assert "cannot be negative" in output


def test_add_item(capsys):
    new_item = {"id": 6, "product_name": "Kimyet", "brands": "Turukwei", "price": 300, "stock": 15, "ingredients_text": ""}
    with patch("builtins.input", side_effect=["Kimyet", "Turukwei", "300", "15"]):
        with patch("cli.requests.request", return_value=fake_response(new_item, 201)) as mock_request:
            cli.add_item()
    assert mock_request.call_args[0][0] == "POST"
    assert mock_request.call_args[1]["json"]["price"] == 300
    assert "Kimyet" in capsys.readouterr().out


def test_add_item_empty_name(capsys):
    with patch("builtins.input", return_value=" "):
        with patch("cli.requests.request") as mock_request:
            cli.add_item()
    mock_request.assert_not_called()
    assert "cannot be empty" in capsys.readouterr().out


def test_update_price(capsys):
    updated = dict(item, price=1200)
    with patch("builtins.input", side_effect=["1", "price", "1200"]):
        with patch("cli.requests.request", return_value=fake_response(updated)) as mock_request:
            cli.update_item()
    assert mock_request.call_args[0][0] == "PATCH"
    assert mock_request.call_args[1]["json"] == {"price": 1200}
    assert "1200" in capsys.readouterr().out


def test_update_invalid_field(capsys):
    with patch("builtins.input", side_effect=["1", "colour"]):
        with patch("cli.requests.request") as mock_request:
            cli.update_item()
    mock_request.assert_not_called()
    assert "Type price or stock" in capsys.readouterr().out


def test_delete_item(capsys):
    with patch("builtins.input", return_value="5"):
        with patch("cli.requests.request", return_value=fake_response({"message": "Item deleted"})) as mock_request:
            cli.delete_item()
    assert mock_request.call_args[0][0] == "DELETE"
    assert "Item deleted" in capsys.readouterr().out


def test_find_on_api(capsys):
    details = {"product_name": "Honey", "brands": "Bee Co", "ingredients_text": "honey"}
    with patch("builtins.input", return_value="honey"):
        with patch("cli.requests.request", return_value=fake_response(details)):
            cli.find_on_api()
    assert "Bee Co" in capsys.readouterr().out


def test_find_on_api_not_found(capsys):
    with patch("builtins.input", return_value="zzzz"):
        with patch("cli.requests.request", return_value=fake_response({"error": "Product not found on OpenFoodFacts"}, 404)):
            cli.find_on_api()
    assert "not found" in capsys.readouterr().out


def test_find_on_api_empty_search(capsys):
    with patch("builtins.input", return_value=""):
        with patch("cli.requests.request") as mock_request:
            cli.find_on_api()
    mock_request.assert_not_called()


def test_add_from_api(capsys):
    added = {"id": 6, "product_name": "Honey", "brands": "Bee Co", "price": 700, "stock": 8, "ingredients_text": "honey"}
    with patch("builtins.input", side_effect=["honey", "700", "8"]):
        with patch("cli.requests.request", return_value=fake_response(added, 201)) as mock_request:
            cli.add_from_api()
    assert mock_request.call_args[1]["json"] == {"query": "honey", "price": 700, "stock": 8}
    assert "Added from OpenFoodFacts" in capsys.readouterr().out


def test_menu_quits_and_handles_invalid_choice(capsys):
    with patch("builtins.input", side_effect=["9", "0"]):
        cli.main()
    assert "Invalid choice" in capsys.readouterr().out
