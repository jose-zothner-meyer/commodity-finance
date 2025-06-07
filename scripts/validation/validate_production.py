#!/usr/bin/env python3
"""
Portfolio Analytics Platform - Production Deployment Validator

This script validates a production deployment of the portfolio analytics platform.
It checks all components: database, cache, web server, and API endpoints.
"""

import requests
import psycopg2
import redis
import subprocess
import sys
import time
import json
from datetime import datetime

class ProductionValidator:
    def __init__(self, base_url="http://localhost", db_config=None):
        self.base_url = base_url.rstrip('/')
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'portfolio_analytics',
            'user': 'portfolio_user',
            'password': 'secure_password_123'
        }
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'tests': {}
        }
        
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"🚀 {text}")
        print(f"{'='*60}")
    
    def print_subheader(self, text):
        print(f"\n🔍 {text}")
        print("-" * 40)
    
    def print_result(self, test_name, status, message=""):
        symbol = "✅" if status else "❌"
        self.results['tests'][test_name] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        print(f"{symbol} {test_name}: {message}")
    
    def check_system_services(self):
        """Check if system services are running"""
        self.print_subheader("System Services Status")
        
        services = [
            'postgresql',
            'redis-server', 
            'nginx',
            'portfolio-analytics'
        ]
        
        all_services_ok = True
        
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    self.print_result(f"Service {service}", True, "Running")
                else:
                    self.print_result(f"Service {service}", False, "Not running")
                    all_services_ok = False
                    
            except Exception as e:
                self.print_result(f"Service {service}", False, f"Check failed: {e}")
                all_services_ok = False
        
        return all_services_ok
    
    def check_database_connection(self):
        """Test PostgreSQL database connection"""
        self.print_subheader("Database Connection")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # Test portfolio tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            tables = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            self.print_result("Database connection", True, f"Connected to PostgreSQL")
            self.print_result("Database tables", True, f"Found {len(tables)} tables")
            return True
            
        except Exception as e:
            self.print_result("Database connection", False, f"Failed: {e}")
            return False
    
    def check_redis_connection(self):
        """Test Redis cache connection"""
        self.print_subheader("Redis Cache Connection")
        
        try:
            r = redis.Redis(host='localhost', port=6379, db=1)
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=10)
            value = r.get('test_key')
            r.delete('test_key')
            
            # Get Redis info
            info = r.info()
            
            self.print_result("Redis connection", True, f"Connected to Redis {info['redis_version']}")
            self.print_result("Redis memory", True, f"Used memory: {info['used_memory_human']}")
            return True
            
        except Exception as e:
            self.print_result("Redis connection", False, f"Failed: {e}")
            return False
    
    def check_web_server(self):
        """Test Nginx web server"""
        self.print_subheader("Web Server")
        
        try:
            # Test basic HTTP response
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                self.print_result("Web server", True, f"Nginx responding (HTTP {response.status_code})")
                
                # Check headers
                security_headers = [
                    'X-Frame-Options',
                    'X-XSS-Protection', 
                    'X-Content-Type-Options'
                ]
                
                headers_ok = True
                for header in security_headers:
                    if header in response.headers:
                        self.print_result(f"Security header {header}", True, response.headers[header])
                    else:
                        self.print_result(f"Security header {header}", False, "Missing")
                        headers_ok = False
                
                return True
            else:
                self.print_result("Web server", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("Web server", False, f"Failed: {e}")
            return False
    
    def check_api_endpoints(self):
        """Test all portfolio analytics API endpoints"""
        self.print_subheader("Portfolio Analytics API Endpoints")
        
        endpoints = [
            ('/api/portfolio/sample', 'GET', None),
            ('/api/portfolio/analyze', 'POST', {
                'portfolio_data': {
                    'GOLD': [100, 105, 110, 108, 112],
                    'SILVER': [25, 26, 24, 27, 28]
                },
                'weights': [0.6, 0.4]
            }),
            ('/api/portfolio/optimize', 'POST', {
                'portfolio_data': {
                    'GOLD': [100, 105, 110, 108, 112],
                    'SILVER': [25, 26, 24, 27, 28]
                },
                'risk_tolerance': 'moderate'
            }),
            ('/api/portfolio/simulate', 'POST', {
                'portfolio_data': {
                    'GOLD': [100, 105, 110, 108, 112],
                    'SILVER': [25, 26, 24, 27, 28]
                },
                'weights': [0.6, 0.4],
                'num_simulations': 100
            })
        ]
        
        all_endpoints_ok = True
        
        for endpoint, method, data in endpoints:
            try:
                start_time = time.time()
                
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                elif method == 'POST':
                    response = requests.post(
                        f"{self.base_url}{endpoint}", 
                        json=data, 
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    # Try to parse JSON response
                    try:
                        json_data = response.json()
                        self.print_result(
                            f"API {endpoint}", 
                            True, 
                            f"OK ({response_time:.0f}ms)"
                        )
                    except json.JSONDecodeError:
                        self.print_result(
                            f"API {endpoint}", 
                            False, 
                            f"Invalid JSON response"
                        )
                        all_endpoints_ok = False
                else:
                    self.print_result(
                        f"API {endpoint}", 
                        False, 
                        f"HTTP {response.status_code}"
                    )
                    all_endpoints_ok = False
                    
            except Exception as e:
                self.print_result(f"API {endpoint}", False, f"Failed: {e}")
                all_endpoints_ok = False
        
        return all_endpoints_ok
    
    def check_performance(self):
        """Test system performance metrics"""
        self.print_subheader("Performance Metrics")
        
        try:
            # Test API response time
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/portfolio/sample", timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if response_time < 1000:  # Less than 1 second
                    self.print_result("API response time", True, f"{response_time:.0f}ms")
                else:
                    self.print_result("API response time", False, f"{response_time:.0f}ms (> 1s)")
                    
                # Check response size
                response_size = len(response.content)
                self.print_result("Response size", True, f"{response_size} bytes")
                
                return response_time < 1000
            else:
                self.print_result("Performance test", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("Performance test", False, f"Failed: {e}")
            return False
    
    def check_security(self):
        """Test security configurations"""
        self.print_subheader("Security Configuration")
        
        security_tests = []
        
        try:
            # Test HTTPS redirect (if not localhost)
            if 'localhost' not in self.base_url and '127.0.0.1' not in self.base_url:
                try:
                    http_url = self.base_url.replace('https://', 'http://')
                    response = requests.get(http_url, allow_redirects=False, timeout=10)
                    
                    if response.status_code in [301, 302] and 'https' in response.headers.get('Location', ''):
                        self.print_result("HTTPS redirect", True, f"HTTP -> HTTPS redirect")
                        security_tests.append(True)
                    else:
                        self.print_result("HTTPS redirect", False, "No HTTPS redirect")
                        security_tests.append(False)
                except:
                    self.print_result("HTTPS redirect", False, "Could not test")
                    security_tests.append(False)
            else:
                self.print_result("HTTPS redirect", True, "Localhost (skip)")
                security_tests.append(True)
            
            # Test firewall status
            try:
                result = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
                if 'Status: active' in result.stdout:
                    self.print_result("Firewall", True, "UFW active")
                    security_tests.append(True)
                else:
                    self.print_result("Firewall", False, "UFW not active")
                    security_tests.append(False)
            except:
                self.print_result("Firewall", False, "Could not check UFW")
                security_tests.append(False)
            
            return all(security_tests)
            
        except Exception as e:
            self.print_result("Security check", False, f"Failed: {e}")
            return False
    
    def generate_report(self):
        """Generate final validation report"""
        self.print_header("Production Deployment Validation Report")
        
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for test in self.results['tests'].values() if test['status'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Test Results Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if success_rate >= 90:
            self.results['overall_status'] = 'EXCELLENT'
            print("🎉 DEPLOYMENT STATUS: EXCELLENT")
            print("   Production deployment is fully operational!")
            
        elif success_rate >= 75:
            self.results['overall_status'] = 'GOOD'
            print("✅ DEPLOYMENT STATUS: GOOD")
            print("   Production deployment is operational with minor issues.")
            
        elif success_rate >= 50:
            self.results['overall_status'] = 'WARNING'
            print("⚠️  DEPLOYMENT STATUS: WARNING")
            print("   Production deployment has significant issues that need attention.")
            
        else:
            self.results['overall_status'] = 'CRITICAL'
            print("❌ DEPLOYMENT STATUS: CRITICAL")
            print("   Production deployment has critical failures.")
        
        print()
        print("📋 Failed Tests:")
        for test_name, test_data in self.results['tests'].items():
            if not test_data['status']:
                print(f"   ❌ {test_name}: {test_data['message']}")
        
        print()
        print("🔗 Quick Access URLs:")
        print(f"   Dashboard: {self.base_url}/")
        print(f"   Sample API: {self.base_url}/api/portfolio/sample")
        print(f"   Health Check: {self.base_url}/health")
        
        # Save detailed report
        with open('production_validation_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📝 Detailed report saved to: production_validation_report.json")
        
        return success_rate >= 75  # Return True if deployment is acceptable
    
    def run_full_validation(self):
        """Run complete production validation"""
        self.print_header("Portfolio Analytics Platform - Production Validation")
        
        print(f"🎯 Target: {self.base_url}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all validation checks
        validation_steps = [
            self.check_system_services,
            self.check_database_connection,
            self.check_redis_connection,
            self.check_web_server,
            self.check_api_endpoints,
            self.check_performance,
            self.check_security
        ]
        
        for step in validation_steps:
            try:
                step()
            except Exception as e:
                print(f"❌ Validation step failed: {e}")
        
        # Generate final report
        return self.generate_report()

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio Analytics Production Deployment Validator')
    parser.add_argument('--url', default='http://localhost', 
                       help='Base URL to test (default: http://localhost)')
    parser.add_argument('--db-host', default='localhost', 
                       help='Database host (default: localhost)')
    parser.add_argument('--db-name', default='portfolio_analytics', 
                       help='Database name (default: portfolio_analytics)')
    parser.add_argument('--db-user', default='portfolio_user', 
                       help='Database user (default: portfolio_user)')
    parser.add_argument('--db-password', default='secure_password_123', 
                       help='Database password')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    validator = ProductionValidator(base_url=args.url, db_config=db_config)
    
    success = validator.run_full_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
