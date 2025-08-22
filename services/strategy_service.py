"""
Strategy service for implementing and managing investment strategies.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from error_handling import StrategyCalculationError

logger = logging.getLogger(__name__)


class StrategyService:
    """Service for managing investment strategies and calculations."""
    
    def __init__(self):
        self.logger = logger
    
    def calculate_gem_strategy(self, results_data: Dict[str, Dict[str, Any]], 
                             equity_etfs: List[str], bond_etfs: List[str]) -> str:
        """
        Calculate GEM strategy recommendation based on ETF performance data.
        
        Args:
            results_data: Dictionary containing ETF performance data
            equity_etfs: List of equity ETF names
            bond_etfs: List of bond ETF names
            
        Returns:
            Strategy recommendation string
            
        Raises:
            StrategyCalculationError: If strategy calculation fails
        """
        try:
            self.logger.info("Calculating GEM strategy recommendation")
            
            # Filter equity ETFs with valid return data
            equity_returns = {
                k: v["return"] for k, v in results_data.items() 
                if k in equity_etfs and v["return"] is not None
            }
            
            if not equity_returns:
                self.logger.warning("No equity ETF data available for decision making")
                return "Brak danych do podjęcia decyzji."

            # Find best performing equity ETF
            best_equity_name = max(equity_returns, key=equity_returns.get)
            best_equity_return = equity_returns[best_equity_name]
            
            self.logger.debug(f"Best equity ETF: {best_equity_name} with return: {best_equity_return}%")
            
            # If best equity ETF has positive return, invest in it
            if best_equity_return > 0:
                recommendation = f"Zainwestuj w {best_equity_name}"
                self.logger.info(f"GEM recommendation: {recommendation} (positive equity return: {best_equity_return}%)")
                return recommendation
            
            # Otherwise, move to safe haven (bonds)
            bond_returns = {
                k: v["return"] for k, v in results_data.items() 
                if k in bond_etfs and v["return"] is not None
            }
            
            if bond_returns:
                best_bond_name = max(bond_returns, key=bond_returns.get)
                best_bond_return = bond_returns[best_bond_name]
                recommendation = f"Zainwestuj w {best_bond_name} (ochrona kapitału)"
                self.logger.info(
                    f"GEM recommendation: {recommendation} "
                    f"(negative equity return: {best_equity_return}%, "
                    f"best bond: {best_bond_name} with return: {best_bond_return}%)"
                )
                return recommendation
            else:
                recommendation = "Brak danych dla obligacji, ale akcje mają ujemną stopę zwrotu. Rozważ gotówkę."
                self.logger.warning(f"GEM recommendation: {recommendation} (no bond data available)")
                return recommendation
                
        except Exception as e:
            error_msg = f"Error calculating GEM strategy: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise StrategyCalculationError(error_msg, strategy="GEM")
    
    def calculate_performance_metrics(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate performance metrics from historical data.
        
        Args:
            historical_data: List of historical price data
            
        Returns:
            Dictionary containing performance metrics
        """
        try:
            if not historical_data or len(historical_data) < 2:
                return {}
            
            prices = [float(point['price']) for point in historical_data if point.get('price')]
            if len(prices) < 2:
                return {}
            
            # Calculate basic metrics
            initial_price = prices[0]
            final_price = prices[-1]
            total_return = (final_price / initial_price - 1) * 100
            
            # Calculate volatility (standard deviation of returns)
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    daily_return = (prices[i] / prices[i-1] - 1) * 100
                    returns.append(daily_return)
            
            volatility = 0.0
            if returns:
                import statistics
                volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
            
            return {
                'total_return': round(total_return, 2),
                'volatility': round(volatility, 2),
                'data_points': len(prices)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def validate_strategy_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.
        
        Args:
            parameters: Dictionary of strategy parameters
            
        Returns:
            True if parameters are valid, False otherwise
        """
        required_params = ['lookback_period', 'rebalance_frequency']
        
        for param in required_params:
            if param not in parameters:
                self.logger.error(f"Missing required parameter: {param}")
                return False
        
        # Validate lookback period
        if not isinstance(parameters['lookback_period'], int) or parameters['lookback_period'] <= 0:
            self.logger.error("Lookback period must be a positive integer")
            return False
        
        # Validate rebalance frequency
        valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        if parameters['rebalance_frequency'] not in valid_frequencies:
            self.logger.error(f"Invalid rebalance frequency. Must be one of: {valid_frequencies}")
            return False
        
        return True
