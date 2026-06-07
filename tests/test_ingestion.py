import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from ingestion.models import CoinMarketRecord
from ingestion.storage import MARKET_DATA_SCHEMA, write_market_data_batch


def make_valid_record(**overrides) -> dict:
    base = {
        "coin_id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "price_usd": 75000.0,
        "market_cap": 1500000000000,
        "vol_24h": 10000000000,
        "price_change_24h_pct": -5,
        "high_24h": 80000.0,
        "low_24h": 70000.0,
        "ingested_at": datetime.now(UTC),
    }
    return {**base, **overrides}


# Data model unit tests


def test_valid_record_pass():
    record = CoinMarketRecord(**make_valid_record())
    assert record.coin_id == "bitcoin"


def test_coin_id_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(coin_id=None))


def test_symbol_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(symbol=None))


def test_name_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(name=None))


def test_coin_id_forced_lowercase():
    record = CoinMarketRecord(**make_valid_record(coin_id=" BITCOIN "))
    assert record.coin_id == "bitcoin"


def test_symbol_forced_lowercase():
    record = CoinMarketRecord(**make_valid_record(symbol=" BTC "))
    assert record.symbol == "btc"


def test_negative_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(price_usd=-1))


def test_zero_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(price_usd=0))


def test_null_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(price_usd=None))


def test_future_timestamp_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(
            **make_valid_record(ingested_at=datetime.now(UTC) + timedelta(days=1))
        )


def test_past_timestamp_ok():
    record = CoinMarketRecord(
        **make_valid_record(ingested_at=datetime.now(UTC) - timedelta(days=1))
    )
    assert record is not None


def test_optional_fields_none_ok():
    record = CoinMarketRecord(
        **make_valid_record(
            market_cap=None,
            vol_24h=None,
            price_change_24h_pct=None,
            high_24h=None,
            low_24h=None,
        )
    )
    assert record is not None


# Parquet writer unit tests


def test_write_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        records = [CoinMarketRecord(**make_valid_record())]
        path = write_market_data_batch(records, tmp, datetime.now(UTC))
        assert path.exists()


def test_write_correct_row_count():
    with tempfile.TemporaryDirectory() as tmp:
        records = [
            CoinMarketRecord(
                **make_valid_record(
                    coin_id=f"coin{i}", symbol=f"C{i}", price_usd=100 + i
                )
            )
            for i in range(5)
        ]
        path = write_market_data_batch(records, tmp, datetime.now(UTC))
        table = pq.read_table(path)
        assert len(table) == 5


def test_write_schema_matches():
    with tempfile.TemporaryDirectory() as tmp:
        records = [
            CoinMarketRecord(
                **make_valid_record(
                    coin_id=f"coin{i}", symbol=f"C{i}", price_usd=100 + i
                )
            )
            for i in range(3)
        ]
        path = write_market_data_batch(records, tmp, datetime.now(UTC))
        table = pq.read_table(path)
        # drop auto-generated partition column before comparing
        table = table.drop(["date"])
        assert table.schema.equals(MARKET_DATA_SCHEMA)


def test_write_empty_records_error():
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(ValueError):
            records = []
            write_market_data_batch(records, tmp, datetime.now(UTC))


# Pipeline integration tests


@pytest.mark.asyncio
async def test_pipeline_writes_parquet():
    raw = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 75000.0}
    ]
    with tempfile.TemporaryDirectory() as tmp:
        with patch(
            "ingestion.pipeline.fetch_top_n_coin_ids",
            new=AsyncMock(return_value=["bitcoin"]),
        ):
            with patch(
                "ingestion.pipeline.fetch_current_market_data",
                new=AsyncMock(return_value=raw),
            ):
                with patch("ingestion.pipeline.DATA_RAW_PATH", tmp):
                    from ingestion.pipeline import run_pipeline

                    await run_pipeline(num_coins=1)
        files = list(Path(tmp).rglob("*.parquet"))
        assert len(files) == 1


@pytest.mark.asyncio
async def test_pipeline_skips_invalid_rows():
    # one valid and one invalid row (zero price)
    raw = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 75000.0},
        {"id": "badcoin", "symbol": "bad", "name": "Badcoin", "current_price": 0},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        with patch(
            "ingestion.pipeline.fetch_top_n_coin_ids",
            new=AsyncMock(return_value=["bitcoin", "badcoin"]),
        ):
            with patch(
                "ingestion.pipeline.fetch_current_market_data",
                new=AsyncMock(return_value=raw),
            ):
                with patch("ingestion.pipeline.DATA_RAW_PATH", tmp):
                    from ingestion.pipeline import run_pipeline

                    await run_pipeline(num_coins=2)
        files = list(Path(tmp).rglob("*.parquet"))
        assert len(files) == 1
        table = pq.read_table(files[0])
        assert len(table) == 1
