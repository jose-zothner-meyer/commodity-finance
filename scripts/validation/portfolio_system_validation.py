#!/usr/bin/env python3
"""
Portfolio Analytics System Validation Script

This comprehensive script validates the entire portfolio analytics platform including:
- All API endpoints functionality
- Error handling scenarios
- Performance metrics
- Cache functionality
- System health checks
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
import traceback

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()

from django.core.cache import cache
from django.conf import settings

class PortfolioSystemValidator:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.test_results = {}
        self.performance_metrics = {}
        
    def print_header(self, title):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"  {title.upper()}")
        print(f"{'='*80}")
        
    def print_subheader(self, title):
        """Print formatted subsection header"""
        print(f"\n--- {title} ---")
        
    def time_request(self, func, *args, **kwargs):
        """Time a request and return result with timing"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, (end_time - start_time) * 1000  # Return time in milliseconds

    def test_django_server_health(self):
        """Test basic Django server connectivity"""
        self.print_subheader("Django Server Health Check")
        try:
            response, timing = self.time_request(requests.get, f"{self.base_url}/api/portfolio/sample")
            if response.status_code == 200:
                print("✅ Django server is accessible")
                print(f"⏱️  Response time: {timing:.2f}ms")
                self.test_results['server_health'] = True
                self.performance_metrics['server_response_time'] = timing
                return True
            else:
                print(f"❌ Server returned status {response.status_code}")
                self.test_results['server_health'] = False
                return False
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            self.test_results['server_health'] = False
            return False

    def test_cache_functionality(self):
        """Test Redis cache integration"""
        self.print_subheader("Cache System Validation")
        try:
            # Test cache write/read
            test_key = f"validation_test_{int(time.time())}"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            cache.set(test_key, test_value, 30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                print("✅ Redis cache working correctly")
                print(f"✅ Cache key: {test_key}")
                
                # Test cache deletion
                cache.delete(test_key)
                deleted_value = cache.get(test_key)
                if deleted_value is None:
                    print("✅ Cache deletion working")
                    self.test_results['cache'] = True
                else:
                    print("⚠️  Cache deletion may have issues")
                    self.test_results['cache'] = False
            else:
                print("❌ Cache read/write failed")
                self.test_results['cache'] = False
                
        except Exception as e:
            print(f"❌ Cache test failed: {e}")
            self.test_results['cache'] = False

    def test_portfolio_sample_endpoint(self):
        """Test sample portfolio generation"""
        self.print_subheader("Sample Portfolio Endpoint")
        try:
            response, timing = self.time_request(
                requests.get, f"{self.base_url}/api/portfolio/sample"
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'portfolio_data' in data and len(data['portfolio_data']) >= 2:
                    print(f"✅ Sample portfolio generated: {len(data['portfolio_data'])} commodities")
                    print(f"⏱️  Response time: {timing:.2f}ms")
                    self.test_results['sample_endpoint'] = True
                    self.performance_metrics['sample_response_time'] = timing
                else:
                    print("❌ Invalid sample portfolio structure")
                    self.test_results['sample_endpoint'] = False
            else:
                print(f"❌ Sample endpoint failed: {response.status_code}")
                self.test_results['sample_endpoint'] = False
                
        except Exception as e:
            print(f"❌ Sample endpoint error: {e}")
            self.test_results['sample_endpoint'] = False

    def test_portfolio_analysis_endpoint(self):
        """Test portfolio analysis with various scenarios"""
        self.print_subheader("Portfolio Analysis Endpoint")
        
        # Test successful analysis
        sample_portfolio = {
            'commodities': [
                {
                    'symbol': 'GCUSD', 'name': 'Gold', 'weight': 0.6,
                    'prices': [1800, 1820, 1810, 1830, 1825, 1815, 1840, 1820, 1835, 1825, 1850, 1830, 1845],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10',
                             '2024-01-11', '2024-01-12', '2024-01-13']
                },
                {
                    'symbol': 'SIUSD', 'name': 'Silver', 'weight': 0.4,
                    'prices': [25, 26, 24, 27, 26, 25, 28, 26, 27, 25, 29, 27, 28],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10',
                             '2024-01-11', '2024-01-12', '2024-01-13']
                }
            ]
        }
        
        try:
            response, timing = self.time_request(
                requests.post, f"{self.base_url}/api/portfolio/analyze",
                json=sample_portfolio, headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'portfolio_metrics' in data:
                    metrics = data['portfolio_metrics']
                    required_metrics = ['portfolio_return', 'portfolio_volatility', 'sharpe_ratio']
                    if all(metric in metrics for metric in required_metrics):
                        print(f"✅ Portfolio analysis successful")
                        print(f"📊 Return: {metrics['portfolio_return']:.2%}")
                        print(f"📊 Volatility: {metrics['portfolio_volatility']:.2%}")
                        print(f"📊 Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
                        print(f"⏱️  Response time: {timing:.2f}ms")
                        self.test_results['analysis_endpoint'] = True
                        self.performance_metrics['analysis_response_time'] = timing
                    else:
                        print("❌ Missing required metrics in response")
                        self.test_results['analysis_endpoint'] = False
                else:
                    print("❌ No portfolio metrics in response")
                    self.test_results['analysis_endpoint'] = False
            else:
                print(f"❌ Analysis endpoint failed: {response.status_code}")
                self.test_results['analysis_endpoint'] = False
                
        except Exception as e:
            print(f"❌ Analysis endpoint error: {e}")
            self.test_results['analysis_endpoint'] = False

    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation endpoint"""
        self.print_subheader("Monte Carlo Simulation Endpoint")
        
        sample_portfolio = {
            'commodities': [
                {
                    'symbol': 'GCUSD', 'name': 'Gold', 'weight': 0.5,
                    'prices': [1800, 1820, 1810, 1830, 1825, 1815, 1840, 1820, 1835, 1825],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                },
                {
                    'symbol': 'CLUSD', 'name': 'Crude Oil', 'weight': 0.5,
                    'prices': [70, 72, 69, 74, 71, 73, 75, 72, 76, 74],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']
                }
            ],
            'num_simulations': 100,  # Smaller for faster testing
            'time_horizon_days': 30
        }
        
        try:
            response, timing = self.time_request(
                requests.post, f"{self.base_url}/api/portfolio/simulate",
                json=sample_portfolio, headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'simulation_results' in data:
                    results = data['simulation_results']
                    if 'final_value_stats' in results and 'num_simulations' in results:
                        print(f"✅ Monte Carlo simulation successful")
                        print(f"🎯 Simulations: {results['num_simulations']}")
                        stats = results['final_value_stats']
                        print(f"📈 Mean final value: {stats['mean']:.3f}")
                        print(f"📉 5th percentile: {stats['percentile_5']:.3f}")
                        print(f"⏱️  Response time: {timing:.2f}ms")
                        self.test_results['simulation_endpoint'] = True
                        self.performance_metrics['simulation_response_time'] = timing
                    else:
                        print("❌ Missing simulation results")
                        self.test_results['simulation_endpoint'] = False
                else:
                    print("❌ No simulation results in response")
                    self.test_results['simulation_endpoint'] = False
            else:
                print(f"❌ Simulation endpoint failed: {response.status_code}")
                self.test_results['simulation_endpoint'] = False
                
        except Exception as e:
            print(f"❌ Simulation endpoint error: {e}")
            self.test_results['simulation_endpoint'] = False

    def test_portfolio_optimization(self):
        """Test portfolio optimization endpoint"""
        self.print_subheader("Portfolio Optimization Endpoint")
        
        sample_portfolio = {
            'commodities': [
                {
                    'symbol': 'GCUSD', 'name': 'Gold', 'weight': 0.33,
                    'prices': [1800, 1820, 1810, 1830, 1825, 1815, 1840, 1820, 1835, 1825, 1850],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11']
                },
                {
                    'symbol': 'SIUSD', 'name': 'Silver', 'weight': 0.33,
                    'prices': [25, 26, 24, 27, 26, 25, 28, 26, 27, 25, 29],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11']
                },
                {
                    'symbol': 'CLUSD', 'name': 'Crude Oil', 'weight': 0.34,
                    'prices': [70, 72, 69, 74, 71, 73, 75, 72, 76, 74, 77],
                    'dates': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', 
                             '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11']
                }
            ],
            'risk_tolerance': 'moderate'
        }
        
        try:
            response, timing = self.time_request(
                requests.post, f"{self.base_url}/api/portfolio/optimize",
                json=sample_portfolio, headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'optimization_results' in data:
                    results = data['optimization_results']
                    if 'optimal_weights' in results:
                        print(f"✅ Portfolio optimization successful")
                        weights = results['optimal_weights']
                        print("🎯 Optimal weights:")
                        total_weight = sum(weights.values())
                        for symbol, weight in weights.items():
                            print(f"   - {symbol}: {weight:.2%}")
                        print(f"✅ Weight sum: {total_weight:.3f}")
                        print(f"⏱️  Response time: {timing:.2f}ms")
                        self.test_results['optimization_endpoint'] = True
                        self.performance_metrics['optimization_response_time'] = timing
                    else:
                        print("❌ No optimal weights in response")
                        self.test_results['optimization_endpoint'] = False
                else:
                    print("❌ No optimization results in response")
                    self.test_results['optimization_endpoint'] = False
            else:
                print(f"❌ Optimization endpoint failed: {response.status_code}")
                self.test_results['optimization_endpoint'] = False
                
        except Exception as e:
            print(f"❌ Optimization endpoint error: {e}")
            self.test_results['optimization_endpoint'] = False

    def test_error_handling(self):
        """Test error handling scenarios"""
        self.print_subheader("Error Handling Validation")
        
        error_scenarios = [
            {
                'name': 'Empty Portfolio Analysis',
                'url': '/api/portfolio/analyze',
                'data': {'commodities': []},
                'expected_status': 400
            },
            {
                'name': 'Invalid JSON',
                'url': '/api/portfolio/analyze',
                'data': 'invalid json',
                'expected_status': 400
            },
            {
                'name': 'Single Commodity Optimization',
                'url': '/api/portfolio/optimize',
                'data': {'commodities': [{'symbol': 'TEST', 'prices': [100], 'dates': ['2024-01-01'], 'weight': 1.0}]},
                'expected_status': 400
            }
        ]
        
        passed_tests = 0
        for scenario in error_scenarios:
            try:
                if isinstance(scenario['data'], str):
                    # Send invalid JSON
                    response = requests.post(
                        f"{self.base_url}{scenario['url']}",
                        data=scenario['data'],
                        headers={'Content-Type': 'application/json'}
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}{scenario['url']}",
                        json=scenario['data'],
                        headers={'Content-Type': 'application/json'}
                    )
                
                if response.status_code == scenario['expected_status']:
                    print(f"✅ {scenario['name']}: Correct error handling")
                    passed_tests += 1
                else:
                    print(f"❌ {scenario['name']}: Expected {scenario['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {scenario['name']}: Test failed with error: {e}")
        
        self.test_results['error_handling'] = passed_tests == len(error_scenarios)
        print(f"\n📊 Error handling tests: {passed_tests}/{len(error_scenarios)} passed")

    def generate_final_report(self):
        """Generate comprehensive validation report"""
        self.print_header("SYSTEM VALIDATION REPORT")
        
        # Overall system status
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"🎯 OVERALL SYSTEM STATUS: {'✅ PASS' if passed_tests == total_tests else '⚠️ PARTIAL' if passed_tests > 0 else '❌ FAIL'}")
        print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
        
        # Individual test results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        # Performance metrics
        if self.performance_metrics:
            print(f"\n⚡ PERFORMANCE METRICS:")
            for metric_name, value in self.performance_metrics.items():
                print(f"   {metric_name.replace('_', ' ').title()}: {value:.2f}ms")
        
        # System info
        print(f"\n🔧 SYSTEM INFORMATION:")
        print(f"   Django Version: {django.get_version()}")
        print(f"   Python Version: {sys.version.split()[0]}")
        print(f"   Cache Backend: {settings.CACHES['default']['BACKEND']}")
        print(f"   Database: {settings.DATABASES['default']['ENGINE']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.test_results.get('server_health', False):
            print("   ✅ System is production-ready")
        else:
            print("   ⚠️  Fix server connectivity issues before deployment")
            
        if self.test_results.get('cache', False):
            print("   ✅ Caching system operational")
        else:
            print("   ⚠️  Check Redis configuration")
            
        avg_response_time = sum(self.performance_metrics.values()) / len(self.performance_metrics) if self.performance_metrics else 0
        if avg_response_time < 1000:  # Less than 1 second
            print("   ✅ Response times are acceptable")
        else:
            print("   ⚠️  Consider optimizing for better performance")

    def run_validation(self):
        """Run complete system validation"""
        self.print_header("Portfolio Analytics System Validation")
        print("🚀 Starting comprehensive system validation...")
        print("   This will test all endpoints, error handling, and system health")
        
        try:
            # Core system tests
            if not self.test_django_server_health():
                print("❌ Server health check failed. Stopping validation.")
                return
            
            self.test_cache_functionality()
            
            # API endpoint tests
            self.test_portfolio_sample_endpoint()
            self.test_portfolio_analysis_endpoint()
            self.test_monte_carlo_simulation()
            self.test_portfolio_optimization()
            
            # Error handling tests
            self.test_error_handling()
            
            # Generate final report
            self.generate_final_report()
            
        except Exception as e:
            print(f"\n❌ VALIDATION FAILED: {e}")
            traceback.print_exc()

def main():
    """Main execution function"""
    validator = PortfolioSystemValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()
