import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

class GemStrategyError(Exception):
    """Base exception for GemStrategy application."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }

class DataFetchError(GemStrategyError):
    """Raised when data fetching fails."""
    
    def __init__(self, message: str, source: str = None, ticker: str = None):
        super().__init__(message, "DATA_FETCH_ERROR", {"source": source, "ticker": ticker})

class DataProcessingError(GemStrategyError):
    """Raised when data processing fails."""
    
    def __init__(self, message: str, operation: str = None, data_type: str = None):
        super().__init__(message, "DATA_PROCESSING_ERROR", {"operation": operation, "data_type": data_type})

class StrategyCalculationError(GemStrategyError):
    """Raised when strategy calculation fails."""
    
    def __init__(self, message: str, strategy: str = None, parameters: Dict[str, Any] = None):
        super().__init__(message, "STRATEGY_CALCULATION_ERROR", {"strategy": strategy, "parameters": parameters})

class ConfigurationError(GemStrategyError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR", {"config_key": config_key})

class ValidationError(GemStrategyError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})

def handle_data_fetch_error(func):
    """Decorator to handle data fetching errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Data fetch error in {func.__name__}: {str(e)}", exc_info=True)
            raise DataFetchError(f"Failed to fetch data: {str(e)}")
    return wrapper

def handle_data_processing_error(func):
    """Decorator to handle data processing errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Data processing error in {func.__name__}: {str(e)}", exc_info=True)
            raise DataProcessingError(f"Failed to process data: {str(e)}")
    return wrapper

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default value if denominator is zero."""
    try:
        if denominator == 0:
            logger.warning(f"Division by zero attempted: {numerator} / {denominator}")
            return default
        return numerator / denominator
    except Exception as e:
        logger.error(f"Error in safe_divide: {str(e)}")
        return default

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, returning default if conversion fails."""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to convert {value} to float: {str(e)}")
        return default

def validate_date_string(date_str: str) -> bool:
    """Validate date string format."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_ticker(ticker: str) -> bool:
    """Validate ticker format."""
    if not ticker or not isinstance(ticker, str):
        return False
    # Basic validation - ticker should be alphanumeric with possible dots
    import re
    return bool(re.match(r'^[A-Za-z0-9.]+$', ticker))

def log_and_raise_error(error: Exception, context: str = None, **kwargs):
    """Log error and raise it with additional context."""
    logger.error(f"Error in {context or 'unknown context'}: {str(error)}", exc_info=True, extra=kwargs)
    raise error

def create_error_response(error: Exception, status_code: int = 500) -> JSONResponse:
    """Create standardized error response."""
    if isinstance(error, GemStrategyError):
        error_data = error.to_dict()
    else:
        error_data = {
            "error": error.__class__.__name__,
            "message": str(error),
            "error_code": "UNKNOWN_ERROR",
            "details": {}
        }
    
    logger.error(f"Returning error response: {error_data}")
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )

# FastAPI exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return create_error_response(exc, exc.status_code)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    logger.warning(f"Validation error: {exc.errors()}")
    error = ValidationError("Request validation failed", details={"validation_errors": exc.errors()})
    return create_error_response(error, 422)

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return create_error_response(exc, 500)

def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("Exception handlers registered successfully")
