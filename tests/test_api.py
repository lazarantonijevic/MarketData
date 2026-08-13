API_KEY = "test-key-for-pytest"
HEADERS = {"X-Api-Key": API_KEY}


# --- /prices ---


def test_get_all_prices_returns_200(client):
    response = client.get("/prices/", headers=HEADERS)
    assert response.status_code == 200


def test_get_all_prices_returns_all_coins(client):
    response = client.get("/prices/", headers=HEADERS)
    data = response.json()
    assert len(data) == 2


def test_all_prices_response_shape(client):
    response = client.get("/prices/", headers=HEADERS)
    coin = response.json()[0]
    assert "coin_id" in coin
    assert "date_day" in coin
    assert "symbol" in coin
    assert "name" in coin
    assert "price_usd" in coin
    assert "total_volume" in coin
    assert "market_cap" in coin
    assert "price_change_24h_pct" in coin
    assert "ma_7d" in coin
    assert "ma_30d" in coin


def test_get_price_by_coin_id_returns_200(client):
    response = client.get("/prices/bitcoin", headers=HEADERS)
    assert response.status_code == 200


def test_get_price_by_coin_id_correct_coin(client):
    response = client.get("/prices/bitcoin", headers=HEADERS)
    assert response.json()["coin_id"] == "bitcoin"


def test_get_price_by_coin_id_case_insensitive(client):
    response = client.get("/prices/BITCOIN", headers=HEADERS)
    assert response.status_code == 200


def test_get_price_unknown_coin_returns_404(client):
    response = client.get("/prices/fakecoin", headers=HEADERS)
    assert response.status_code == 404


def test_get_prices_missing_api_key_returns_422(client):
    response = client.get("/prices/")
    assert response.status_code == 422


def test_get_prices_wrong_api_key_returns_401(client):
    response = client.get("/prices/", headers={"X-Api-Key": "wrong"})
    assert response.status_code == 401


# --- /ohlcv ---


def test_get_ohlcv_returns_200(client):
    response = client.get("/ohlcv/bitcoin", headers=HEADERS)
    assert response.status_code == 200


def test_get_ohlcv_returns_list(client):
    response = client.get("/ohlcv/bitcoin", headers=HEADERS)
    assert isinstance(response.json(), list)


def test_get_ohlcv_correct_row_count(client):
    response = client.get("/ohlcv/bitcoin", headers=HEADERS)
    assert len(response.json()) == 2


def test_get_ohlcv_response_shape(client):
    response = client.get("/ohlcv/bitcoin", headers=HEADERS)
    candle = response.json()[0]
    assert "coin_id" in candle
    assert "symbol" in candle
    assert "name" in candle
    assert "date_day" in candle
    assert "open" in candle
    assert "high" in candle
    assert "low" in candle
    assert "close" in candle
    assert "total_volume" in candle
    assert "market_cap" in candle
    assert "row_count" in candle


def test_get_ohlcv_ordered_ascending(client):
    response = client.get("/ohlcv/bitcoin", headers=HEADERS)
    dates = [row["date_day"] for row in response.json()]
    assert dates == sorted(dates)


def test_get_ohlcv_unknown_coin_returns_404(client):
    response = client.get("/ohlcv/fakefake", headers=HEADERS)
    assert response.status_code == 404


def test_get_ohlcv_case_insensitive(client):
    response = client.get("/ohlcv/BITCOIN", headers=HEADERS)
    assert response.status_code == 200


def test_get_ohlcv_missing_api_key_returns_422(client):
    response = client.get("/ohlcv/BITCOIN")
    assert response.status_code == 422


def test_get_ohlcv_wrong_api_key_returns_401(client):
    response = client.get("/ohlcv/BITCOIN", headers={"X-Api-Key": "nope"})
    assert response.status_code == 401
