from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
from io import StringIO
from curl_cffi import requests as cffi_requests
from requests.exceptions import RequestException
from config import TICKERS, BENCHMARK_TICKER, EQUITY_ETFS, BOND_ETFS
from logging_config import configure_logging_from_env, get_logger
from error_handling import (
    DataFetchError, DataProcessingError, StrategyCalculationError,
    ValidationError, handle_data_fetch_error, handle_data_processing_error,
    safe_divide, safe_float_conversion, validate_date_string, validate_ticker,
    register_exception_handlers
)
from services.strategy_service import StrategyService
from services.data_service import DataService
from config_package.settings import get_settings
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from logging import Logger

# Configure logging
configure_logging_from_env()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    debug=settings.api.debug,
    docs_url="/docs" if settings.api.debug else None,
    redoc_url="/redoc" if settings.api.debug else None,
    openapi_tags=[
        {
            "name": "strategy",
            "description": "Investment strategy operations"
        },
        {
            "name": "data",
            "description": "ETF data operations"
        },
        {
            "name": "analysis",
            "description": "Performance analysis operations"
        }
    ]
)

# Register exception handlers
register_exception_handlers(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logger.info("GemStrategy application starting up...")
logger.info(f"Environment: {settings.environment}")
logger.info(f"Debug mode: {settings.api.debug}")
logger.info(f"API version: {settings.api.version}")

class StooqDataFetcher:
    """Klasa odpowiedzialna za pobieranie i cachowanie danych z serwisu Stooq."""
    
    def __init__(self, cache_ttl_hours: int = 4) -> None:
        self.CACHE_TTL: timedelta = timedelta(hours=cache_ttl_hours)
        self.last_cache_reset: datetime = datetime.now()
        self.logger: Logger = get_logger(__name__)
        self.logger.info(f"StooqDataFetcher initialized with cache TTL: {cache_ttl_hours} hours")

    @lru_cache(maxsize=32)
    def _get_12m_return_stooq_cached(self, ticker: str, reference_date_str: str) -> Tuple[Optional[float], Optional[datetime.date], Optional[datetime.date], Optional[List[Dict[str, Any]]]]:
        """
        Pobiera dane dzienne z Stooq i liczy zwrot % za okres 1 roku.
        Wyniki są cachowane w pamięci, aby unikać wielokrotnych zapytań do API.
        """
        # Validate inputs
        if not validate_ticker(ticker):
            self.logger.error(f"Invalid ticker format: {ticker}")
            return None, None, None, None
            
        if not validate_date_string(reference_date_str):
            self.logger.error(f"Invalid date format: {reference_date_str}")
            return None, None, None, None
        
        try:
            reference_date = datetime.strptime(reference_date_str, '%Y-%m-%d')
        except ValueError as e:
            self.logger.error(f"Failed to parse date {reference_date_str}: {e}")
            return None, None, None, None
            
        url = f"https://stooq.pl/q/d/l/?s={ticker}&i=d"
        self.logger.debug(f"Fetching data for {ticker} from {url}")
        
        try:
            response = cffi_requests.get(url, impersonate="chrome110")
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
        except RequestException as e:
            self.logger.error(f"Network error while fetching {ticker} from Stooq: {e}")
            return None, None, None, None
        except Exception as e:
            self.logger.error(f"Data processing error for {ticker} from Stooq: {e}")
            return None, None, None, None

        if df.empty or ("Close" not in df.columns and "Zamkniecie" not in df.columns):
            self.logger.error(f"No data or invalid format for {ticker}")
            return None, None, None, None
        
        close_col = "Close" if "Close" in df.columns else "Zamkniecie"
        
        try:
            df["Data"] = pd.to_datetime(df["Data"])
            df = df.sort_values(by="Data")
        except Exception as e:
            self.logger.error(f"Error processing date column for {ticker}: {e}")
            return None, None, None, None
        
        # Ustalenie 12-miesięcznego okresu do analizy
        end_date = reference_date - pd.DateOffset(months=1)
        start_date = end_date - pd.DateOffset(years=1) + pd.DateOffset(days=1)
        
        self.logger.debug(f"Analyzing period {start_date.date()} - {end_date.date()} for {ticker}")
        
        df_12m = df[(df["Data"] >= start_date) & (df["Data"] <= end_date)]

        if df_12m.empty:
            self.logger.warning(f"No data in period {start_date.date()} - {end_date.date()} for {ticker}")
            return None, None, None, None
        
        first_price = safe_float_conversion(df_12m.iloc[0][close_col])
        last_price = safe_float_conversion(df_12m.iloc[-1][close_col])

        if first_price <= 0 or last_price <= 0:
            self.logger.warning(f"Invalid prices for {ticker}: first={first_price}, last={last_price}")
            return None, None, None, None

        # Obliczenie zwrotu procentowego
        try:
            return_percentage = safe_divide(last_price, first_price, 1.0) - 1
            return_percentage *= 100
            
            historical_data = df_12m[['Data', close_col]].rename(columns={'Data': 'date', close_col: 'price'})
            
            self.logger.info(f"Successfully calculated return for {ticker}: {return_percentage:.2f}%")
            
            return return_percentage, df_12m.iloc[0]["Data"].date(), df_12m.iloc[-1]["Data"].date(), historical_data.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error calculating return for {ticker}: {e}")
            return None, None, None, None

    def get_return(self, ticker: str, ref_date_str: str) -> Tuple[Optional[float], Optional[datetime.date], Optional[datetime.date], Optional[List[Dict[str, Any]]]]:
        """Sprawdza, czy cache nie wygasł i zwraca dane z cachowanej funkcji."""
        if datetime.now() - self.last_cache_reset > self.CACHE_TTL:
            self._get_12m_return_stooq_cached.cache_clear()
            self.last_cache_reset = datetime.now()
            self.logger.info("Cache has been reset")
        return self._get_12m_return_stooq_cached(ticker, ref_date_str)

# Initialize services
data_fetcher = StooqDataFetcher(cache_ttl_hours=settings.data.cache_ttl_hours)
data_service = DataService(data_fetcher)
strategy_service = StrategyService()

logger.info("Services initialized successfully")
logger.info(f"Data fetcher cache TTL: {settings.data.cache_ttl_hours} hours")

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    """
    Display the main form for date selection.
    
    Returns:
        HTML template with date selection form
    """
    logger.debug("GET request to main form")
    today_date = datetime.today().strftime('%Y-%m-%d')
    return templates.TemplateResponse(request, "index.html", {"results": None, "choice": None, "benchmark": None, "today_date": today_date})

@app.post("/", response_class=HTMLResponse)
async def calculate(
    request: Request, 
    reference_date_str: str = Form(alias="reference_date", description="Reference date for analysis in YYYY-MM-DD format")
):
    """
    Main endpoint that orchestrates calculations and returns results.
    
    Args:
        reference_date_str: Reference date for the analysis
        
    Returns:
        HTML template with analysis results and recommendations
    """
    logger.info(f"Processing calculation request for reference date: {reference_date_str}")
    
    try:
        # Validate input
        if not validate_date_string(reference_date_str):
            logger.error(f"Invalid date format: {reference_date_str}")
            raise ValidationError("Invalid date format", field="reference_date", value=reference_date_str)
        
        # Get data using services
        results_data = data_service.get_all_etf_returns(reference_date_str)
        benchmark_result = data_service.get_benchmark_data(reference_date_str)
        choice = strategy_service.calculate_gem_strategy(results_data, EQUITY_ETFS, BOND_ETFS)
        
        logger.info(f"Strategy calculation completed. Recommendation: {choice}")

        # Prepare template data using services
        results_for_template = data_service.prepare_template_data(results_data)
        chart_data = data_service.prepare_chart_data(results_data, benchmark_result)
        
        logger.info(f"Template data prepared: {len(results_for_template)} results, {len(chart_data)} chart datasets")

        return templates.TemplateResponse(request, "index.html", {
            "results": results_for_template, 
            "choice": choice, 
            "benchmark": benchmark_result, 
            "today_date": reference_date_str,
            "chart_data": json.dumps(chart_data, default=str)
        })
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return templates.TemplateResponse(request, "index.html", {
            "results": None, 
            "choice": f"Błąd: {e.message}", 
            "benchmark": None, 
            "today_date": reference_date_str,
            "chart_data": "[]"
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in calculation endpoint: {e}", exc_info=True)
        return templates.TemplateResponse(request, "index.html", {
            "results": None, 
            "choice": "Wystąpił nieoczekiwany błąd. Spróbuj ponownie później.", 
            "benchmark": None, 
            "today_date": reference_date_str,
            "chart_data": "[]"
        })

# New API endpoints for better functionality
@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "version": settings.api.version,
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/etfs", tags=["data"])
async def get_etf_list():
    """
    Get list of available ETFs.
    
    Returns:
        List of ETF information
    """
    etf_list = []
    for name, ticker in TICKERS.items():
        etf_type = "equity" if name in EQUITY_ETFS else "bond"
        etf_list.append({
            "name": name,
            "ticker": ticker,
            "type": etf_type
        })
    
    return {
        "etfs": etf_list,
        "total": len(etf_list),
        "equity_count": len(EQUITY_ETFS),
        "bond_count": len(BOND_ETFS)
    }

@app.get("/api/strategy/parameters", tags=["strategy"])
async def get_strategy_parameters():
    """
    Get current GEM strategy parameters.
    
    Returns:
        Strategy parameters and configuration
    """
    return {
        "strategy_name": "Global Equities Momentum (GEM)",
        "description": "Momentum-based strategy that invests in the best performing equity ETF or moves to bonds if all equities are negative",
        "parameters": {
            "lookback_period": "12 months",
            "rebalance_frequency": "monthly",
            "equity_etfs": EQUITY_ETFS,
            "bond_etfs": BOND_ETFS,
            "benchmark": BENCHMARK_TICKER
        },
        "cache_settings": {
            "ttl_hours": settings.data.cache_ttl_hours,
            "max_retries": settings.data.max_retries
        }
    }
