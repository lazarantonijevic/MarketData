# MarketData
Cryptocurrency Market Data Platform

## Initial Project Goals
- The goal is to build a platform which incorporates an end-to-end data pipeline, collecting cryptocurrency market data from public APIs, analyzing and transforming the data, and presenting it in a usable format via a user-friendly dashboard.
- This project is founded on the core principles of data engineering and analytics, but the initial focus of this project will be on system design and architecture, as well as incorporating best practices related to the development, testing and deployment.

## Initial Project Architecture and Tech-Stack Plan
The system will consist of several key components:
1. **Input/Data Ingestion Layer**: collects data from public APIs(CoinGecko, Binance...), handles data collection logic (scheduling, batching, orchestrating around rate limits...), validates data schema and stores the raw data.
2. **Raw Data Storage Layer**: Stores the raw unprocessed data.
3. **Data Processing/Transformation Layer**: Reads raw data, cleans it, analyzes it and transforms it into a usable format(OHLC prices, volume, moving averages, anomaly indicators...).
4. **Serving Layer**: Opens API endpoints making the data available to the frontend and handles all related logic.
5. **Presentation/Dashboard Layer**: A user-friendly intuitive interface presenting the processed data.

- Prefect will be used for orchestration and scheduling.
- Pydantic will be used for data validation.
- Due to the mostly analytical data workload, an OLAP DB makes more sense then a traditional OLTP DB. In this case, Parquet and DuckDB will be used for the data storage and querying.
- dbt will be used for data transformation and testing.
- FastAPI will be used for the API serving layer.
- Streamlit will be used for the frontend dashboard.
- Docker and Docker Compose will be used for containerization.