# Alpha Vantage API Rate Limiting

## Overview
The Alpha Vantage API has strict rate limits, especially for free tier users. When these limits are exceeded, the API returns a different response format that needs special handling.

## Rate Limit Behavior

### Normal Response Format
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "value": "75.23"
    }
  ]
}
```

### Rate Limited Response Format
```json
{
  "Information": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day. Please subscribe to any of the premium plans at https://www.alphavantage.co/premium/ to instantly remove all daily rate limits."
}
```

## How Our Application Handles Rate Limits

### 1. Detection
The application detects rate limit responses by checking for the `"Information"` key in the API response.

### 2. Error Response Structure
When a rate limit is detected, the application returns:
```json
{
  "dates": [],
  "values": [],
  "error": "API rate limit exceeded"
}
```

### 3. HTTP Status Codes
- **Before Fix**: HTTP 500 (Internal Server Error) - Application crashed
- **After Fix**: HTTP 429 (Too Many Requests) - Proper rate limit response

### 4. User Experience
Instead of seeing a server error, users now receive:
```json
{
  "error": "API rate limit exceeded",
  "type": "vendor",
  "endpoint": "get_commodities",
  "params": {...}
}
```

## Testing Rate Limits

### API Endpoint Test
```bash
curl -X GET "http://localhost:8001/api/commodities?name=WTI&start=2024-01-01&end=2024-01-30&source=alpha_vantage"
```

### Expected Response (Rate Limited)
```json
{
  "error": "API rate limit exceeded",
  "type": "vendor", 
  "endpoint": "get_commodities",
  "params": {
    "name": ["WTI"],
    "start": ["2024-01-01"],
    "end": ["2024-01-30"],
    "source": ["alpha_vantage"]
  }
}
```

## Implementation Details

### Files Modified
1. `energy_finance/data_ingest.py` - Added rate limit detection in `AlphaVantageAPIClient`
2. `energy_finance/views.py` - Added error response handling in `get_commodities()`

### Key Changes
- Detection of `"Information"` field in Alpha Vantage responses
- Graceful error handling instead of KeyError crashes
- Proper HTTP status code (429) for rate limit scenarios
- Clear error messaging for end users

## Recommendations

### For Free Tier Users
- Limit Alpha Vantage requests to avoid hitting daily limits
- Consider implementing request caching
- Use alternative data sources when possible

### For Premium Users
- Rate limits are removed with premium subscriptions
- Monitor usage to stay within subscription limits
- Implement retry logic with exponential backoff for temporary issues

## Alternative Data Sources
The application supports multiple data sources:
- `api_ninjas` - Alternative commodity data provider
- `fmp` - Financial Modeling Prep API
- `commodity_price_api` - Specialized commodity pricing API

Users can switch between sources using the `source` parameter in API requests.
