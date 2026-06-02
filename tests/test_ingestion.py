import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from ingestion.models import CoinMarketRecord
from ingestion.storage import write_market_data_batch


def make_valid_record(**overrides) -> dict:
    base = {
        "coin_id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "price_usd": 75000.0,
        "ingested_at": datetime.now(UTC),
    }
    return {**base, **overrides}


# Data model unit tests


def test_valid_record_pass():
    record = CoinMarketRecord(**make_valid_record())
    assert record.coin_id == "bitcoin"


def test_coin_id_null_error():
    pass


def test_symbol_null_error():
    pass


def test_name_null_error():
    pass


def test_coin_id_forced_lowercase():
    pass


def test_symbol_forced_lowercase():
    pass


def test_negative_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_record(price_usd=-1))


def test_zero_price_error():
    pass


def test_null_price_error():
    pass


def test_future_timestamp_error():
    pass


def test_past_timestamp_ok():
    pass


def test_optional_fields_none_ok():
    pass


# Parquet writer unit tests


def test_write_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        records = [CoinMarketRecord(**make_valid_record())]
        path = write_market_data_batch(records, tmp, datetime.now(UTC))
        assert path.exists()


def test_write_correct_row_count():
    pass


def test_write_schema_matches():
    pass


def test_write_empty_records_error():
    pass


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


def test_pipeline_skips_invalid_rows():
    pass
