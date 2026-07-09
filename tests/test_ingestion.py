import asyncio
import json
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import duckdb
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from ingestion.backfill import backfill_coin
from ingestion.models import CoinHistoryRecord, CoinMarketRecord, PipelineRun
from ingestion.storage import (
    MARKET_DATA_SCHEMA,
    log_pipeline_run,
    write_market_data_batch,
)
from ingestion.universe import get_coin, initialize_universe, load_universe


def make_valid_market_record(**overrides) -> dict:
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


def make_valid_history_record(**overrides) -> dict:
    base = {
        "coin_id": "bitcoin",
        "timestamp_ms": 1782864000000,
        "price_usd": 75000.0,
        "market_cap": 1500000000000,
        "total_volume": 10000000000,
    }
    return {**base, **overrides}


# Data model unit tests


def test_valid_record_pass():
    record = CoinMarketRecord(**make_valid_market_record())
    assert record.coin_id == "bitcoin"


def test_coin_id_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(coin_id=None))


def test_symbol_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(symbol=None))


def test_name_null_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(name=None))


def test_coin_id_forced_lowercase():
    record = CoinMarketRecord(**make_valid_market_record(coin_id=" BITCOIN "))
    assert record.coin_id == "bitcoin"


def test_symbol_forced_lowercase():
    record = CoinMarketRecord(**make_valid_market_record(symbol=" BTC "))
    assert record.symbol == "btc"


def test_negative_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(price_usd=-1))


def test_zero_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(price_usd=0))


def test_null_price_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(**make_valid_market_record(price_usd=None))


def test_future_timestamp_error():
    with pytest.raises(ValidationError):
        CoinMarketRecord(
            **make_valid_market_record(
                ingested_at=datetime.now(UTC) + timedelta(days=1)
            )
        )


def test_past_timestamp_ok():
    record = CoinMarketRecord(
        **make_valid_market_record(ingested_at=datetime.now(UTC) - timedelta(days=1))
    )
    assert record is not None


def test_optional_fields_none_ok():
    record = CoinMarketRecord(
        **make_valid_market_record(
            market_cap=None,
            vol_24h=None,
            price_change_24h_pct=None,
            high_24h=None,
            low_24h=None,
        )
    )
    assert record is not None


def test_history_record_valid():
    record = CoinHistoryRecord(**make_valid_history_record())
    assert record.coin_id == "bitcoin"


def test_history_record_zero_price_error():
    with pytest.raises(ValidationError):
        CoinHistoryRecord(**make_valid_history_record(price_usd=0))


def test_history_record_neg_price_error():
    with pytest.raises(ValidationError):
        CoinHistoryRecord(**make_valid_history_record(price_usd=-1))


def test_to_market_record_converts():
    hist = CoinHistoryRecord(**make_valid_history_record())
    market = hist.to_market_record(symbol="btc", name="Bitcoin")
    assert market.coin_id == "bitcoin"
    assert market.symbol == "btc"
    assert market.name == "Bitcoin"
    assert market.price_usd == hist.price_usd
    assert market.market_cap == hist.market_cap
    assert market.vol_24h == hist.total_volume


def test_to_market_record_no_optionals():
    hist = CoinHistoryRecord(
        **make_valid_history_record(market_cap=None, total_volume=None)
    )
    market = hist.to_market_record(symbol="btc", name="Bitcoin")
    assert market.market_cap is None
    assert market.vol_24h is None


def test_to_market_record_timestamp_conversion():
    hist = CoinHistoryRecord(**make_valid_history_record(timestamp_ms=1782864000000))
    market = hist.to_market_record(symbol="btc", name="Bitcoin")
    assert market.ingested_at == datetime(2026, 7, 1, tzinfo=UTC)


def test_pipeline_run_valid():
    run = PipelineRun(
        run_id="some-uuid",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        status="success",
        records_written=10,
        records_skipped=0,
        duration_seconds=1.5,
    )
    assert run.status == "success"
    assert run.error_message is None


def test_pipeline_run_invalid_status_error():
    with pytest.raises(ValidationError):
        PipelineRun(
            run_id="some-uuid",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            status="something",
            records_written=0,
            records_skipped=0,
            duration_seconds=0.0,
        )


# Parquet writer unit tests


def test_write_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        records = [CoinMarketRecord(**make_valid_market_record())]
        path = write_market_data_batch(records, tmp, datetime.now(UTC))
        assert path.exists()


def test_write_correct_row_count():
    with tempfile.TemporaryDirectory() as tmp:
        records = [
            CoinMarketRecord(
                **make_valid_market_record(
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
                **make_valid_market_record(
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


# Pipeline run logging unit tests


def test_log_pipeline_run_creates_table():
    run = PipelineRun(
        run_id="some-uuid",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        status="success",
        records_written=5,
        records_skipped=0,
        duration_seconds=1.0,
        error_message=None,
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "pipeline_runs.duckdb")
        log_pipeline_run(run, db_path=db_path)

        con = duckdb.connect(db_path)
        res = con.execute("SELECT * FROM pipeline_runs").fetchall()
        con.close()

        assert len(res) == 1
        assert res[0][0] == "some-uuid"
        assert res[0][3] == "success"


def test_log_pipeline_run_appends():
    run1 = PipelineRun(
        run_id="uuid-1",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        status="success",
        records_written=5,
        records_skipped=0,
        duration_seconds=1.0,
        error_message=None,
    )
    run2 = PipelineRun(
        run_id="uuid-2",
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        status="failed",
        records_written=0,
        records_skipped=5,
        duration_seconds=2.0,
        error_message="Some error",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "pipeline_runs.duckdb")
        log_pipeline_run(run1, db_path=db_path)
        log_pipeline_run(run2, db_path=db_path)

        con = duckdb.connect(db_path)
        res = con.execute("SELECT run_id FROM pipeline_runs ORDER BY run_id").fetchall()
        con.close()

        assert len(res) == 2
        assert res[0][0] == "uuid-1"
        assert res[1][0] == "uuid-2"


# Universe unit tests


def test_init_universe_creates_file():
    coins = [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "universe.json"
        with patch("ingestion.universe.UNIVERSE_FILE_PATH", tmp_path):
            with patch(
                "ingestion.universe.fetch_top_n_coins",
                new=AsyncMock(return_value=coins),
            ):
                asyncio.run(initialize_universe(top_n=1))

                assert tmp_path.exists()
                content = json.loads(tmp_path.read_text(encoding="utf-8"))
                assert len(content) == 1
                assert content[0]["id"] == "bitcoin"


def test_init_universe_prevents_overwrite():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "universe.json"
        fake_path.write_text("[]", encoding="utf-8")
        with patch("ingestion.universe.UNIVERSE_FILE_PATH", fake_path):
            with pytest.raises(FileExistsError):
                asyncio.run(initialize_universe(top_n=1))


def test_load_universe_returns_list():
    coins = [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "universe.json"
        tmp_path.write_text(json.dumps(coins), encoding="utf-8")
        with patch("ingestion.universe.UNIVERSE_FILE_PATH", tmp_path):
            from ingestion.universe import load_universe

            res = load_universe()
            assert res == coins


def test_load_universe_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "missing_universe.json"
        with patch("ingestion.universe.UNIVERSE_FILE_PATH", tmp_path):
            with pytest.raises(FileNotFoundError):
                load_universe()


def test_get_coin_metadata():
    universe = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    ]
    coin = get_coin(universe, "ethereum")
    assert coin["symbol"] == "eth"

    with pytest.raises(KeyError):
        get_coin(universe, "dogecoin")


# Backfill integration tests


@pytest.mark.asyncio
async def test_backfill_writes_parquet():
    mock_history = {
        "prices": [[1782864000000, 75000.0]],
        "market_caps": [[1782864000000, 1500000000000]],
        "total_volumes": [[1782864000000, 10000000000]],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch(
            "ingestion.backfill.fetch_coin_history",
            new=AsyncMock(return_value=mock_history),
        ):
            written = await backfill_coin(
                "bitcoin", "btc", "Bitcoin", days=1, base_path=tmp_path
            )
            assert written == 1

            files = list(tmp_path.rglob("*.parquet"))
            assert len(files) == 1


@pytest.mark.asyncio
async def test_backfill_skips_existing():
    mock_history = {
        "prices": [[1782864000000, 75000.0]],
        "market_caps": [[1782864000000, 1500000000000]],
        "total_volumes": [[1782864000000, 10000000000]],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch("ingestion.backfill.check_partition_exists", return_value=True):
            with patch(
                "ingestion.backfill.fetch_coin_history",
                new=AsyncMock(return_value=mock_history),
            ):
                written = await backfill_coin(
                    "bitcoin", "btc", "Bitcoin", days=1, base_path=tmp_path
                )
                assert written == 0
                files = list(tmp_path.rglob("*.parquet"))
                assert len(files) == 0


# Pipeline integration tests


@pytest.mark.asyncio
async def test_pipeline_writes_parquet():
    raw = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 75000.0}
    ]
    with tempfile.TemporaryDirectory() as tmp:
        with patch(
            "ingestion.pipeline.load_universe",
            return_value=[{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}],
        ):
            with patch(
                "ingestion.pipeline.fetch_current_market_data",
                new=AsyncMock(return_value=raw),
            ):
                with patch("ingestion.pipeline.DATA_RAW_PATH", tmp):
                    from ingestion.pipeline import run_pipeline

                    written, skipped = await run_pipeline()
        assert written == 1
        assert skipped == 0
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
            "ingestion.pipeline.load_universe",
            return_value=[
                {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
                {"id": "badcoin", "symbol": "bad", "name": "Badcoin"},
            ],
        ):
            with patch(
                "ingestion.pipeline.fetch_current_market_data",
                new=AsyncMock(return_value=raw),
            ):
                with patch("ingestion.pipeline.DATA_RAW_PATH", tmp):
                    from ingestion.pipeline import run_pipeline

                    written, skipped = await run_pipeline()
        assert written == 1
        assert skipped == 1
        files = list(Path(tmp).rglob("*.parquet"))
        assert len(files) == 1
        table = pq.read_table(files[0])
        assert len(table) == 1
