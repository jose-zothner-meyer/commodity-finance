#!/usr/bin/env python3
"""
Advanced Portfolio Analytics Module

This module provides comprehensive portfolio management capabilities including:
- Multi-commodity portfolio analysis
- Risk metrics calculation (VaR, CVaR, Sharpe Ratio)
- Correlation analysis and diversification metrics
- Position sizing and optimization
- Monte Carlo simulation for risk assessment
"""

import numpy as np
from typing import List, Dict, Optional, Any
from scipy.optimize import minimize
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalyzer:
    """Advanced portfolio analytics with risk management capabilities"""
    
    def __init__(self):
        self.portfolio_data = {}
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
    def add_commodity(self, symbol: str, prices: List[float], dates: List[str], 
                     weight: float = 1.0) -> bool:
        """Add commodity data to portfolio"""
        try:
            if not prices or not dates or len(prices) != len(dates):
                logger.warning("Invalid data for %s", symbol)
                return False
                
            # Calculate returns
            price_array = np.array(prices)
            returns = np.diff(price_array) / price_array[:-1]
            
            self.portfolio_data[symbol] = {
                'prices': prices,
                'dates': dates,
                'returns': returns.tolist(),
                'weight': weight,
                'current_price': prices[-1] if prices else 0,
                'volatility': np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0  # Annualized
            }
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.error("Error adding commodity %s: %s", symbol, e)
            return False
    
    def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            if not self.portfolio_data:
                return {'error': 'No portfolio data available'}
            
            # Combine all returns into matrix
            returns_matrix = []
            symbols = list(self.portfolio_data.keys())
            weights = []
            
            for symbol in symbols:
                returns_matrix.append(self.portfolio_data[symbol]['returns'])
                weights.append(self.portfolio_data[symbol]['weight'])
            
            # Normalize weights
            weights = np.array(weights)
            weights = weights / np.sum(weights)
            
            # Align return series (take minimum length)
            min_length = min(len(returns) for returns in returns_matrix)
            aligned_returns = np.array([returns[-min_length:] for returns in returns_matrix])
            
            if min_length < 10:  # Need minimum data for meaningful analysis
                return {'error': 'Insufficient data for portfolio analysis'}
            
            # Portfolio returns
            portfolio_returns = np.dot(weights, aligned_returns)
            
            # Calculate metrics
            metrics = {
                'portfolio_return': float(np.mean(portfolio_returns) * 252),  # Annualized
                'portfolio_volatility': float(np.std(portfolio_returns) * np.sqrt(252)),
                'sharpe_ratio': self._calculate_sharpe_ratio(portfolio_returns),
                'var_95': self._calculate_var(portfolio_returns, confidence=0.95),
                'var_99': self._calculate_var(portfolio_returns, confidence=0.99),
                'cvar_95': self._calculate_cvar(portfolio_returns, confidence=0.95),
                'max_drawdown': self._calculate_max_drawdown(portfolio_returns),
                'correlation_matrix': self._calculate_correlation_matrix(aligned_returns, symbols),
                'diversification_ratio': self._calculate_diversification_ratio(aligned_returns, weights),
                'symbols': symbols,
                'weights': weights.tolist(),
                'individual_metrics': self._get_individual_metrics(),
                'risk_decomposition': self._calculate_risk_decomposition(aligned_returns, weights)
            }
            
            return metrics
            
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.error("Error calculating portfolio metrics: %s", e)
            return {'error': f'Portfolio calculation failed: {str(e)}'}
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        try:
            annual_return = np.mean(returns) * 252
            annual_vol = np.std(returns) * np.sqrt(252)
            if annual_vol == 0:
                return 0.0
            return float((annual_return - self.risk_free_rate) / annual_vol)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        try:
            return float(np.percentile(returns, (1 - confidence) * 100))
        except (ValueError, IndexError):
            return 0.0
    
    def _calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        try:
            var = self._calculate_var(returns, confidence)
            cvar_returns = returns[returns <= var]
            return float(np.mean(cvar_returns)) if len(cvar_returns) > 0 else var
        except (ValueError, IndexError):
            return 0.0
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative = np.cumprod(1 + returns)
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak) / peak
            return float(np.min(drawdown))
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _calculate_correlation_matrix(self, returns_matrix: np.ndarray, symbols: List[str]) -> Dict:
        """Calculate correlation matrix between assets"""
        try:
            corr_matrix = np.corrcoef(returns_matrix)
            
            # Convert to dictionary format for JSON serialization
            correlation_dict = {}
            for i, symbol1 in enumerate(symbols):
                correlation_dict[symbol1] = {}
                for j, symbol2 in enumerate(symbols):
                    correlation_dict[symbol1][symbol2] = float(corr_matrix[i, j])
            
            return correlation_dict
        except (ValueError, IndexError):
            return {}
    
    def _calculate_diversification_ratio(self, returns_matrix: np.ndarray, weights: np.ndarray) -> float:
        """Calculate diversification ratio"""
        try:
            # Individual volatilities
            individual_vols = np.array([np.std(returns) for returns in returns_matrix])
            weighted_avg_vol = np.dot(weights, individual_vols)
            
            # Portfolio volatility
            portfolio_returns = np.dot(weights, returns_matrix)
            portfolio_vol = np.std(portfolio_returns)
            
            if portfolio_vol == 0:
                return 1.0
                
            return float(weighted_avg_vol / portfolio_vol)
        except (ValueError, ZeroDivisionError):
            return 1.0
    
    def _get_individual_metrics(self) -> Dict[str, Dict]:
        """Get individual commodity metrics"""
        individual_metrics = {}
        
        for symbol, data in self.portfolio_data.items():
            if len(data['returns']) > 1:
                returns = np.array(data['returns'])
                individual_metrics[symbol] = {
                    'annual_return': float(np.mean(returns) * 252),
                    'volatility': data['volatility'],
                    'sharpe_ratio': self._calculate_sharpe_ratio(returns),
                    'current_price': data['current_price'],
                    'weight': data['weight']
                }
            
        return individual_metrics
    
    def _calculate_risk_decomposition(self, returns_matrix: np.ndarray, weights: np.ndarray) -> Dict:
        """Calculate risk contribution by asset"""
        try:
            # Calculate covariance matrix
            cov_matrix = np.cov(returns_matrix)
            
            # Portfolio variance
            portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
            
            # Marginal contribution to risk
            marginal_contrib = np.dot(cov_matrix, weights)
            
            # Component contribution to risk
            component_contrib = weights * marginal_contrib
            
            # Percentage contribution
            risk_contrib = component_contrib / portfolio_var if portfolio_var > 0 else np.zeros_like(component_contrib)
            
            return {
                'marginal_contribution': marginal_contrib.tolist(),
                'component_contribution': component_contrib.tolist(),
                'percentage_contribution': risk_contrib.tolist()
            }
        except (ValueError, ZeroDivisionError):
            return {}

class MonteCarloSimulator:
    """Monte Carlo simulation for portfolio risk assessment"""
    
    def __init__(self, portfolio_analyzer: PortfolioAnalyzer):
        self.portfolio_analyzer = portfolio_analyzer
    
    def simulate_portfolio_paths(self, num_simulations: int = 1000, 
                                time_horizon: int = 252) -> Dict[str, Any]:
        """Run Monte Carlo simulation for portfolio paths"""
        try:
            if not self.portfolio_analyzer.portfolio_data:
                return {'error': 'No portfolio data for simulation'}
            
            # Prepare data
            symbols = list(self.portfolio_analyzer.portfolio_data.keys())
            weights = np.array([self.portfolio_analyzer.portfolio_data[s]['weight'] for s in symbols])
            weights = weights / np.sum(weights)  # Normalize
            
            # Calculate historical statistics
            returns_matrix = []
            for symbol in symbols:
                returns_matrix.append(self.portfolio_analyzer.portfolio_data[symbol]['returns'])
            
            min_length = min(len(returns) for returns in returns_matrix)
            aligned_returns = np.array([returns[-min_length:] for returns in returns_matrix])
            
            # Calculate mean returns and covariance matrix
            mean_returns = np.mean(aligned_returns, axis=1)
            cov_matrix = np.cov(aligned_returns)
            
            # Run simulations
            simulation_results = []
            final_values = []
            
            for _ in range(num_simulations):
                # Generate random returns using multivariate normal distribution
                simulated_returns = np.random.multivariate_normal(
                    mean_returns, cov_matrix, time_horizon
                )
                
                # Calculate portfolio returns
                portfolio_returns = np.dot(simulated_returns, weights)
                
                # Calculate cumulative value (starting from 1)
                cumulative_value = np.cumprod(1 + portfolio_returns)
                simulation_results.append(cumulative_value.tolist())
                final_values.append(cumulative_value[-1])
            
            # Calculate simulation statistics
            final_values = np.array(final_values)
            
            results = {
                'num_simulations': num_simulations,
                'time_horizon_days': time_horizon,
                'simulation_paths': simulation_results[:100],  # Return first 100 paths for visualization
                'final_value_stats': {
                    'mean': float(np.mean(final_values)),
                    'std': float(np.std(final_values)),
                    'percentile_5': float(np.percentile(final_values, 5)),
                    'percentile_25': float(np.percentile(final_values, 25)),
                    'percentile_50': float(np.percentile(final_values, 50)),
                    'percentile_75': float(np.percentile(final_values, 75)),
                    'percentile_95': float(np.percentile(final_values, 95))
                },
                'probability_of_loss': float(np.sum(final_values < 1.0) / len(final_values)),
                'expected_return': float(np.mean(final_values) - 1),
                'var_95_simulation': float(np.percentile(final_values, 5) - 1),
                'cvar_95_simulation': float(np.mean(final_values[final_values <= np.percentile(final_values, 5)]) - 1)
            }
            
            return results
            
        except (ValueError, TypeError, np.linalg.LinAlgError) as e:
            logger.error("Monte Carlo simulation error: %s", e)
            return {'error': f'Simulation failed: {str(e)}'}

class PortfolioOptimizer:
    """Modern Portfolio Theory optimization"""
    
    def __init__(self, portfolio_analyzer: PortfolioAnalyzer):
        self.portfolio_analyzer = portfolio_analyzer
    
    def optimize_portfolio(self, target_return: Optional[float] = None,
                          risk_tolerance: str = 'moderate') -> Dict[str, Any]:
        """Optimize portfolio weights for maximum Sharpe ratio or target return"""
        try:
            if not self.portfolio_analyzer.portfolio_data:
                return {'error': 'No portfolio data for optimization'}
            
            symbols = list(self.portfolio_analyzer.portfolio_data.keys())
            n_assets = len(symbols)
            
            if n_assets < 2:
                return {'error': 'Need at least 2 assets for optimization'}
            
            # Prepare return data
            returns_matrix = []
            for symbol in symbols:
                returns_matrix.append(self.portfolio_analyzer.portfolio_data[symbol]['returns'])
            
            min_length = min(len(returns) for returns in returns_matrix)
            aligned_returns = np.array([returns[-min_length:] for returns in returns_matrix])
            
            # Calculate expected returns and covariance matrix
            expected_returns = np.mean(aligned_returns, axis=1) * 252  # Annualized
            cov_matrix = np.cov(aligned_returns) * 252  # Annualized
            
            # Set up optimization
            initial_weights = np.array([1/n_assets] * n_assets)
            bounds = tuple((0, 1) for _ in range(n_assets))  # No short selling
            constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]  # Weights sum to 1
            
            # Risk tolerance adjustment
            risk_multipliers = {'conservative': 0.5, 'moderate': 1.0, 'aggressive': 1.5}
            risk_multiplier = risk_multipliers.get(risk_tolerance, 1.0)
            
            if target_return is not None:
                # Optimize for minimum risk given target return
                constraints.append({
                    'type': 'eq', 
                    'fun': lambda w: np.dot(w, expected_returns) - target_return
                })
                
                def risk_objective(weights):
                    return np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                
                objective = risk_objective
            else:
                # Optimize for maximum Sharpe ratio
                def sharpe_objective(weights):
                    portfolio_return = np.dot(weights, expected_returns)
                    portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                    if portfolio_risk == 0:
                        return -np.inf
                    sharpe = (portfolio_return - self.portfolio_analyzer.risk_free_rate) / portfolio_risk
                    return -sharpe * risk_multiplier  # Negative because we minimize
                
                objective = sharpe_objective
            
            # Run optimization
            result = minimize(objective, initial_weights, method='SLSQP',
                            bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_weights = result.x
                
                # Calculate metrics for optimized portfolio
                opt_return = np.dot(optimal_weights, expected_returns)
                opt_risk = np.sqrt(np.dot(optimal_weights, np.dot(cov_matrix, optimal_weights)))
                opt_sharpe = (opt_return - self.portfolio_analyzer.risk_free_rate) / opt_risk if opt_risk > 0 else 0
                
                optimization_results = {
                    'success': True,
                    'optimal_weights': {symbols[i]: float(optimal_weights[i]) for i in range(n_assets)},
                    'expected_annual_return': float(opt_return),
                    'expected_annual_risk': float(opt_risk),
                    'expected_sharpe_ratio': float(opt_sharpe),
                    'risk_tolerance': risk_tolerance,
                    'target_return': target_return,
                    'weight_changes': self._calculate_weight_changes(symbols, optimal_weights)
                }
                
                return optimization_results
            else:
                return {'error': f'Optimization failed: {result.message}'}
                
        except (ValueError, TypeError, np.linalg.LinAlgError) as e:
            logger.error("Portfolio optimization error: %s", e)
            return {'error': f'Optimization failed: {str(e)}'}
    
    def _calculate_weight_changes(self, symbols: List[str], optimal_weights: np.ndarray) -> Dict[str, Dict]:
        """Calculate weight changes from current to optimal"""
        current_weights = np.array([self.portfolio_analyzer.portfolio_data[s]['weight'] for s in symbols])
        current_weights = current_weights / np.sum(current_weights)  # Normalize
        
        weight_changes = {}
        for i, symbol in enumerate(symbols):
            weight_changes[symbol] = {
                'current_weight': float(current_weights[i]),
                'optimal_weight': float(optimal_weights[i]),
                'change': float(optimal_weights[i] - current_weights[i]),
                'percentage_change': float((optimal_weights[i] - current_weights[i]) / current_weights[i] * 100) if current_weights[i] > 0 else 0
            }
        
        return weight_changes

def clean_portfolio_values(values: List[Any]) -> List[float]:
    """Clean and validate portfolio data values"""
    cleaned = []
    for val in values:
        try:
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                cleaned.append(float(val))
            else:
                cleaned.append(0.0)
        except (ValueError, TypeError):
            cleaned.append(0.0)
    return cleaned
