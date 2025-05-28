import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Set your test parameters here
MARKET = 'DE-LU'  # Germany-Luxembourg
# Use specific dates for testing
START_DATE = '2024-05-26'  # Yesterday
END_DATE = '2024-05-27'    # Today

def main():
    # Your ENTSO-E security token
    security_token = '178d5b47-b29a-4c22-b1a7-32cf48883304'

    # ENTSO-E area codes
    market_map = {
        'DE-LU': '10Y1001A1001A83F',  # Germany-Luxembourg
        'FR': '10YFR-RTE------C',    # France
        'ES': '10YES-REE------0',    # Spain
        'IT': '10YIT-GRTN-----B',    # Italy
        'AT': '10YAT-APG------L',    # Austria
    }
    
    domain = market_map.get(MARKET, MARKET)
    # Format dates as YYYYMMDDHHMM (UTC)
    start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
    end_date = datetime.strptime(END_DATE, '%Y-%m-%d')
    period_start = start_date.strftime('%Y%m%d0000')  # Start at 00:00
    period_end = end_date.strftime('%Y%m%d0000')      # End at 00:00 next day
    
    url = 'https://web-api.tp.entsoe.eu/api'
    params = {
        'documentType': 'A65',  # Load forecast
        'in_Domain': domain,
        'out_Domain': domain,
        'outBiddingZone_Domain': domain,  # Required for load forecast
        'periodStart': period_start,
        'periodEnd': period_end,
        'securityToken': security_token,
        'processType': 'A01'  # Day ahead
    }
    
    print("\nTest Configuration:")
    print(f"Market: {MARKET}")
    print(f"Domain: {domain}")
    print(f"Period Start: {period_start}")
    print(f"Period End: {period_end}")
    print("\nMaking API request...")
    
    try:
        r = requests.get(url, params=params)
        print(f"\nStatus Code: {r.status_code}")
        
        if r.status_code == 200:
            try:
                root = ET.fromstring(r.content)
                print("✓ XML parsed successfully")
                print(f"Root tag: {root.tag}")
                
                # Try to extract load forecast data
                print("\nAttempting to extract load forecast data...")
                # Define the namespace
                ns = {'ns': 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:0'}
                
                # Find all time series
                time_series = root.findall('.//ns:TimeSeries', ns)
                if time_series:
                    print(f"\nFound {len(time_series)} time series")
                    for ts in time_series[:1]:  # Show first time series as example
                        period = ts.find('.//ns:Period', ns)
                        if period is not None:
                            print("\nLoad forecast points:")
                            for point in period.findall('.//ns:Point', ns):
                                position = point.find('ns:position', ns).text
                                quantity = point.find('ns:quantity', ns).text
                                print(f"Position: {position}, Quantity: {quantity} MW")
                else:
                    print("\nNo time series found in response")
                    print("\nFull response content:")
                    print(r.content.decode(errors='replace'))
            except ET.ParseError as e:
                print("✗ XML Parse Error:", e)
                print("\nRaw response content:")
                print(r.content.decode(errors='replace'))
        else:
            print("✗ Error Response:")
            print(r.content.decode(errors='replace'))
            
    except requests.exceptions.RequestException as e:
        print("✗ Request failed:", e)

if __name__ == "__main__":
    main() 