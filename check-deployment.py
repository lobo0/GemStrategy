#!/usr/bin/env python3
"""
Deployment status checker for GemStrategy application.
Checks health endpoints and provides deployment information.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

def check_endpoint(url: str, endpoint: str = "") -> Dict[str, Any]:
    """Check a specific endpoint and return status information."""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        response = requests.get(full_url, timeout=10)
        return {
            "url": full_url,
            "status_code": response.status_code,
            "response_time": response.elapsed.total_seconds(),
            "success": response.status_code == 200,
            "content_type": response.headers.get("content-type", ""),
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "url": full_url,
            "error": str(e),
            "success": False,
            "timestamp": datetime.now().isoformat()
        }

def check_health_endpoint(url: str) -> Dict[str, Any]:
    """Check the health endpoint and return detailed health information."""
    try:
        response = requests.get(f"{url.rstrip('/')}/api/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            return {
                "url": f"{url}/api/health",
                "status": "healthy",
                "data": health_data,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "url": f"{url}/api/health",
                "status": "unhealthy",
                "status_code": response.status_code,
                "timestamp": datetime.now().isoformat()
            }
    except requests.exceptions.RequestException as e:
        return {
            "url": f"{url}/api/health",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def check_api_endpoints(url: str) -> Dict[str, Any]:
    """Check various API endpoints for functionality."""
    endpoints = [
        "api/etfs",
        "api/strategy/parameters",
        "",  # Root endpoint
    ]
    
    results = {}
    for endpoint in endpoints:
        results[endpoint or "root"] = check_endpoint(url, endpoint)
    
    return results

def generate_deployment_report(url: str) -> Dict[str, Any]:
    """Generate a comprehensive deployment report."""
    print(f"🔍 Checking deployment at: {url}")
    print("=" * 50)
    
    # Check health
    print("🏥 Checking health endpoint...")
    health_status = check_health_endpoint(url)
    
    # Check API endpoints
    print("🔌 Checking API endpoints...")
    api_status = check_api_endpoints(url)
    
    # Generate report
    report = {
        "deployment_url": url,
        "check_timestamp": datetime.now().isoformat(),
        "health_status": health_status,
        "api_endpoints": api_status,
        "overall_status": "healthy" if health_status.get("status") == "healthy" else "unhealthy"
    }
    
    return report

def print_report(report: Dict[str, Any]) -> None:
    """Print a formatted deployment report."""
    print("\n📊 DEPLOYMENT STATUS REPORT")
    print("=" * 50)
    print(f"🌐 URL: {report['deployment_url']}")
    print(f"⏰ Checked: {report['check_timestamp']}")
    print(f"📈 Overall Status: {report['overall_status'].upper()}")
    
    # Health status
    print(f"\n🏥 Health Endpoint:")
    health = report['health_status']
    if health.get('status') == 'healthy':
        print(f"   ✅ Status: {health['status']}")
        print(f"   ⚡ Response Time: {health['response_time']:.3f}s")
        if 'data' in health:
            print(f"   📋 Version: {health['data'].get('version', 'N/A')}")
            print(f"   🌍 Environment: {health['data'].get('environment', 'N/A')}")
    else:
        print(f"   ❌ Status: {health.get('status', 'unknown')}")
        if 'error' in health:
            print(f"   🚨 Error: {health['error']}")
    
    # API endpoints
    print(f"\n🔌 API Endpoints:")
    for name, status in report['api_endpoints'].items():
        if status.get('success'):
            print(f"   ✅ {name}: {status['status_code']} ({status['response_time']:.3f}s)")
        else:
            print(f"   ❌ {name}: {status.get('error', f'HTTP {status.get("status_code", "N/A")}')}")
    
    print("\n" + "=" * 50)

def main():
    """Main function to run deployment checks."""
    if len(sys.argv) != 2:
        print("Usage: python check-deployment.py <deployment-url>")
        print("Example: python check-deployment.py https://your-app.vercel.app")
        print("Example: python check-deployment.py https://your-app.appspot.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    try:
        report = generate_deployment_report(url)
        print_report(report)
        
        # Save report to file
        filename = f"deployment-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n💾 Report saved to: {filename}")
        
        # Exit with appropriate code
        if report['overall_status'] == 'healthy':
            print("\n✅ Deployment is healthy!")
            sys.exit(0)
        else:
            print("\n❌ Deployment has issues!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
