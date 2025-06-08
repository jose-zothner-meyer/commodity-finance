#!/usr/bin/env python3
"""
Advanced Commodity & Energy Analytics Platform
Portfolio Analytics Demo & Testing Script

This script demonstrates and tests all portfolio analytics features:
1. Portfolio Risk Analysis
2. Monte Carlo Simulation
3. Portfolio Optimization
4. Sample Portfolio Generation
"""

import os
import sys
import requests
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Try to setup Django, but continue even if it fails
DJANGO_AVAILABLE = False
try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Django modules not available: {e}")

# Try to import pandas and numpy, with fallbacks
try:
    import pandas as pd
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    print("Warning: pandas/numpy not available - using mock data")
    NUMPY_AVAILABLE = False


class PortfolioDemo:
    """Portfolio Analytics Testing and Demo Class"""
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.sample_portfolio = {
            'commodities': [
                {
                    'symbol': 'GCUSD',
                    'name': 'Gold',
                    'weight': 0.25,
                    'prices': [1800, 1820, 1810, 1830, 1825, 1815, 1840, 1820, 1835, 1825],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                },
                {
                    'symbol': 'SIUSD',
                    'name': 'Silver',
                    'weight': 0.25,
                    'prices': [25, 26, 24, 27, 26, 25, 28, 26, 27, 25],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                },
                {
                    'symbol': 'CLUSD',
                    'name': 'Crude Oil',
                    'weight': 0.25,
                    'prices': [75, 76, 74, 77, 76, 75, 78, 76, 77, 75],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                },
                {
                    'symbol': 'NGUSD',
                    'name': 'Natural Gas',
                    'weight': 0.25,
                    'prices': [3.5, 3.6, 3.4, 3.7, 3.6, 3.5, 3.8, 3.6, 3.7, 3.5],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                }
            ]
        }
    
    def print_header(self, title):
        """Print formatted section header"""
        print("\n" + "="*80)
        print(f"  {title.upper()}")
        print("="*80)
        
    def print_subheader(self, title):
        """Print formatted subsection header"""
        print(f"\n--- {title} ---")
        
    def test_portfolio_endpoints(self):
        """Test all portfolio API endpoints"""
        self.print_header("Testing Portfolio Analytics API Endpoints")
        
        # Test sample portfolio generation
        self.print_subheader("1. Sample Portfolio Generation")
        try:
            response = requests.get(f"{self.base_url}/api/portfolio/sample/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Sample Portfolio API: SUCCESS")
                portfolio_data = data.get('portfolio_data', data.get('commodities', []))
                print(f"Generated portfolio with {len(portfolio_data)} commodities")
                
                if portfolio_data:
                    # Update sample portfolio with real data from API
                    self.sample_portfolio = {
                        'commodities': [
                            {
                                'symbol': item['symbol'],
                                'name': item.get('name', item['symbol']),
                                'weight': item.get('weight', 1.0 / len(portfolio_data)),
                                'prices': item['prices'][:20],
                                'dates': item['dates'][:20]
                            }
                            for item in portfolio_data[:4]
                        ]
                    }
                    
                    # Normalize weights
                    total_weight = sum(c['weight'] for c in self.sample_portfolio['commodities'])
                    for commodity in self.sample_portfolio['commodities']:
                        commodity['weight'] = commodity['weight'] / total_weight
                        
                    print(f"Using real portfolio data: {[c['symbol'] for c in self.sample_portfolio['commodities']]}")
                else:
                    print("⚠️  No portfolio data in response, using default sample")
            else:
                print(f"❌ Sample Portfolio API: FAILED ({response.status_code})")
                
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"❌ Sample Portfolio API error: {e}")
        
        # Test portfolio analysis
        self.print_subheader("2. Portfolio Analysis")
        try:
            response = requests.post(
                f"{self.base_url}/api/portfolio/analyze/",
                json=self.sample_portfolio,
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ Portfolio Analysis API: SUCCESS")
                
                metrics = data.get('portfolio_metrics', {})
                if 'error' in metrics:
                    print(f"❌ PortfolioAnalyzer: {metrics['error']}")
                else:
                    print("✅ PortfolioAnalyzer: SUCCESS")
                    print(f"Portfolio Return: {metrics.get('portfolio_return', 0):.2%}")
                    print(f"Portfolio Volatility: {metrics.get('portfolio_volatility', 0):.2%}")
                    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
                    print(f"VaR (95%): {metrics.get('var_95', 0):.2%}")
            else:
                print(f"❌ Portfolio Analysis API: FAILED ({response.status_code})")
                
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"❌ Portfolio Analysis API error: {e}")
            
        # Test Monte Carlo simulation
        self.print_subheader("3. Monte Carlo Simulation")
        try:
            sim_data = {
                **self.sample_portfolio,
                'num_simulations': 1000,
                'time_horizon': 252
            }
            response = requests.post(
                f"{self.base_url}/api/portfolio/simulate/",
                json=sim_data,
                timeout=20
            )
            if response.status_code == 200:
                data = response.json()
                print("✅ Monte Carlo Simulation API: SUCCESS")
                
                simulation_results = data.get('simulation_results', {})
                if 'error' in simulation_results:
                    print(f"❌ MonteCarloSimulator: {simulation_results['error']}")
                else:
                    print("✅ MonteCarloSimulator: SUCCESS")
                    print(f"Simulations: {simulation_results.get('num_simulations', 0)}")
                    print(f"Time Horizon: {simulation_results.get('time_horizon', 0)} days")
                    
                    percentiles = simulation_results.get('percentiles', {})
                    if percentiles:
                        print(f"5th Percentile: {percentiles.get('5th', 0):.2%}")
                        print(f"95th Percentile: {percentiles.get('95th', 0):.2%}")
                    else:
                        print("⚠️  Final value stats not available")
            else:
                print(f"❌ Monte Carlo Simulation API: FAILED ({response.status_code})")
                
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"❌ Monte Carlo Simulation API error: {e}")
            
        # Test portfolio optimization
        self.print_subheader("4. Portfolio Optimization")
        try:
            # Test optimization with different risk tolerances
            for risk_tolerance in ['conservative', 'moderate', 'aggressive']:
                opt_data = {
                    **self.sample_portfolio,
                    'risk_tolerance': risk_tolerance
                }
                response = requests.post(
                    f"{self.base_url}/api/portfolio/optimize/",
                    json=opt_data,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    optimization_result = data.get('optimization_result', {})
                    
                    if 'error' in optimization_result:
                        print(f"❌ {risk_tolerance.capitalize()}: {optimization_result['error']}")
                    else:
                        print(f"✅ {risk_tolerance.capitalize()} Portfolio:")
                        print(f"  Expected Return: {optimization_result.get('expected_return', 0):.2%}")
                        print(f"  Portfolio Risk: {optimization_result.get('portfolio_risk', 0):.2%}")
                        
                        # Show top weights
                        weights_dict = optimization_result.get('weights', {})
                        if weights_dict:
                            top_weights = dict(list(weights_dict.items())[:3])
                            print(f"  Top weights: {top_weights}")
                else:
                    print(f"❌ {risk_tolerance.capitalize()}: HTTP {response.status_code}")
                    
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"❌ Portfolio Optimization API error: {e}")
    
    def run_performance_tests(self):
        """Run performance tests on portfolio analytics components"""
        self.print_header("Performance Testing")
        
        if not DJANGO_AVAILABLE:
            print("⚠️  Django not available - skipping performance tests")
            return
            
        # Create mock data for performance testing
        if NUMPY_AVAILABLE:
            np.random.seed(42)
            dates = pd.date_range('2023-01-01', periods=252, freq='D')
            returns_data = {}
            for commodity in self.sample_portfolio['commodities']:
                symbol = commodity['symbol']
                returns_data[symbol] = np.random.normal(0.001, 0.02, 252)
            returns_df = pd.DataFrame(returns_data, index=dates)
            weights = [c['weight'] for c in self.sample_portfolio['commodities']]
        else:
            print("⚠️  NumPy/Pandas not available - using simplified mock data")
            returns_df = None
            weights = [0.25, 0.25, 0.25, 0.25]
        
        # Test analysis performance
        self.print_subheader("1. Portfolio Analysis Performance")
        start_time = time.time()
        try:
            if DJANGO_AVAILABLE and returns_df is not None:
                from apps.core.portfolio import PortfolioAnalyzer
                analyzer = PortfolioAnalyzer(returns_df, weights)
                _ = analyzer.calculate_risk_metrics()
                analysis_time = time.time() - start_time
                print(f"✅ Analysis completed in {analysis_time:.3f} seconds")
            else:
                print("⚠️  Using mock analysis for performance test")
                time.sleep(0.1)  # Simulate processing time
                analysis_time = time.time() - start_time
                print(f"✅ Mock analysis completed in {analysis_time:.3f} seconds")
        except ImportError as e:
            print(f"❌ Analysis performance test failed: {e}")
        
        # Test simulation performance
        self.print_subheader("2. Monte Carlo Simulation Performance")
        start_time = time.time()
        try:
            if DJANGO_AVAILABLE and returns_df is not None:
                from apps.core.portfolio import MonteCarloSimulator
                simulator = MonteCarloSimulator(returns_df, weights)
                _ = simulator.run_simulation(num_simulations=1000)
                simulation_time = time.time() - start_time
                print(f"✅ Simulation (1000 runs) completed in {simulation_time:.3f} seconds")
            else:
                print("⚠️  Using mock simulation for performance test")
                time.sleep(0.2)  # Simulate processing time
                simulation_time = time.time() - start_time
                print(f"✅ Mock simulation completed in {simulation_time:.3f} seconds")
        except ImportError as e:
            print(f"❌ Simulation performance test failed: {e}")
        
        # Test optimization performance
        self.print_subheader("3. Portfolio Optimization Performance")
        start_time = time.time()
        try:
            if DJANGO_AVAILABLE and returns_df is not None:
                from apps.core.portfolio import PortfolioOptimizer
                optimizer = PortfolioOptimizer(returns_df)
                _ = optimizer.optimize_portfolio(risk_tolerance='moderate')
                optimization_time = time.time() - start_time
                print(f"✅ Optimization completed in {optimization_time:.3f} seconds")
            else:
                print("⚠️  Using mock optimization for performance test")
                time.sleep(0.15)  # Simulate processing time
                optimization_time = time.time() - start_time
                print(f"✅ Mock optimization completed in {optimization_time:.3f} seconds")
        except ImportError as e:
            print(f"❌ Optimization performance test failed: {e}")

def main():
    """Main demo execution"""
    print("="*80)
    print("  COMMODITY TRACKER - PORTFOLIO ANALYTICS DEMO")
    print("="*80)
    print(f"Django Available: {DJANGO_AVAILABLE}")
    print(f"NumPy/Pandas Available: {NUMPY_AVAILABLE}")
    
    demo = PortfolioDemo()
    
    try:
        # Test API endpoints
        demo.test_portfolio_endpoints()
        
        # Run performance tests
        demo.run_performance_tests()
        
        print("\n" + "="*80)
        print("  DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except (ImportError, ValueError, RuntimeError) as e:
        print(f"\n\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()
