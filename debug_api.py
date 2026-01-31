import requests
import json

url = "http://localhost:8000/api/strategies/rsi_reversal/run"

payload = {
    "coin": "DOGE/USDT",
    "days": 90,
    "timeframe": "1h",
    "initial_balance": 10000,
    "use_compound": True,
    "sizing_method": "fixo",
    "include_fees": False,
    "fee_rate": 0.0,
    "params": {}
}

try:
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 422:
        print("Validation Error Detail:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Response:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
