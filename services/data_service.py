"""
Data service for managing data fetching and processing operations.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO
import logging
from error_handling import DataFetchError, DataProcessingError
from config import TICKERS, BENCHMARK_TICKER

logger = logging.getLogger(__name__)


class DataService:
    """Service for managing data operations."""
    
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.logger = logger
    
    def get_all_etf_returns(self, ref_date_str: str) -> Dict[str, Dict[str, Any]]:
        """
        Get returns and historical data for all defined ETFs.
        
        Args:
            ref_date_str: Reference date string in YYYY-MM-DD format
            
        Returns:
            Dictionary containing ETF data
        """
        self.logger.info(f"Fetching returns for all ETFs with reference date: {ref_date_str}")
        results = {}
        
        for name, ticker in TICKERS.items():
            self.logger.debug(f"Processing ETF: {name} ({ticker})")
            try:
                ret, start_date, end_date, historical_data = self.data_fetcher.get_return(ticker, ref_date_str)
                results[name] = {
                    "ticker": name,
                    "return": ret,
                    "start": start_date,
                    "end": end_date,
                    "historical_data": historical_data
                }
                self.logger.debug(f"Successfully processed {name}: return={ret}, period={start_date} to {end_date}")
            except Exception as e:
                self.logger.error(f"Error processing ETF {name}: {e}")
                results[name] = {
                    "ticker": name,
                    "return": None,
                    "start": None,
                    "end": None,
                    "historical_data": None
                }
        
        self.logger.info(f"Completed fetching returns for {len(results)} ETFs")
        return results
    
    def get_benchmark_data(self, ref_date_str: str) -> Dict[str, Any]:
        """
        Get benchmark return and historical data.
        
        Args:
            ref_date_str: Reference date string in YYYY-MM-DD format
            
        Returns:
            Dictionary containing benchmark data
        """
        self.logger.info(f"Fetching benchmark return for {BENCHMARK_TICKER} with reference date: {ref_date_str}")
        
        try:
            bench_ret, bench_start, bench_end, historical_data = self.data_fetcher.get_return(BENCHMARK_TICKER, ref_date_str)
            
            if bench_ret is not None:
                bench_ret_rounded = round(bench_ret, 2)
                self.logger.debug(f"Benchmark return: {bench_ret_rounded}% for period {bench_start} to {bench_end}")
            else:
                bench_ret_rounded = None
                self.logger.warning("Benchmark return is None")
            
            return {
                "name": "S&P 500 (SPY)",
                "return": bench_ret_rounded,
                "start": bench_start,
                "end": bench_end,
                "historical_data": historical_data
            }
        except Exception as e:
            self.logger.error(f"Error fetching benchmark return: {e}")
            return {
                "name": "S&P 500 (SPY)",
                "return": None,
                "start": None,
                "end": None,
                "historical_data": None
            }
    
    def prepare_chart_data(self, results_data: Dict[str, Dict[str, Any]], 
                          benchmark_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare data for chart visualization.
        
        Args:
            results_data: ETF performance data
            benchmark_data: Benchmark performance data
            
        Returns:
            List of chart datasets
        """
        chart_data = []
        
        # Add ETF data
        for name, data in results_data.items():
            if data.get("historical_data"):
                chart_data.append({
                    "name": name,
                    "data": data["historical_data"]
                })
        
        # Add benchmark data
        if benchmark_data.get("historical_data"):
            chart_data.append({
                "name": benchmark_data["name"],
                "data": benchmark_data["historical_data"]
            })
        
        self.logger.debug(f"Prepared chart data with {len(chart_data)} datasets")
        return chart_data
    
    def prepare_template_data(self, results_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare data for template rendering.
        
        Args:
            results_data: ETF performance data
            
        Returns:
            List of template-ready data
        """
        template_data = []
        
        for name, data in results_data.items():
            try:
                return_value = round(data["return"], 2) if data["return"] is not None else None
                template_data.append({
                    "ticker": name,
                    "return": return_value,
                    "start": data["start"],
                    "end": data["end"]
                })
                
                self.logger.debug(f"Processed {name}: return={return_value}")
                
            except Exception as e:
                self.logger.error(f"Error processing template data for {name}: {e}")
                template_data.append({
                    "ticker": name,
                    "return": None,
                    "start": None,
                    "end": None
                })
        
        self.logger.info(f"Template data prepared: {len(template_data)} results")
        return template_data
    
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate data quality and completeness.
        
        Args:
            data: Data to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'has_returns': False,
            'has_dates': False,
            'has_historical_data': False,
            'data_complete': False
        }
        
        try:
            # Check if returns exist
            validation_results['has_returns'] = data.get('return') is not None
            
            # Check if dates exist
            validation_results['has_dates'] = (
                data.get('start') is not None and 
                data.get('end') is not None
            )
            
            # Check if historical data exists
            validation_results['has_historical_data'] = (
                data.get('historical_data') is not None and 
                len(data.get('historical_data', [])) > 0
            )
            
            # Overall completeness
            validation_results['data_complete'] = all([
                validation_results['has_returns'],
                validation_results['has_dates'],
                validation_results['has_historical_data']
            ])
            
        except Exception as e:
            self.logger.error(f"Error validating data quality: {e}")
        
        return validation_results
