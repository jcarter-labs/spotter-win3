"""Live diagnostic: verify the real POTA public spot API endpoint and
response shape before writing any parser code (Constitution rule 3 —
verify, don't assume the URL/JSON format from memory).
"""

import json

import requests

URL = "https://api.pota.app/spot/activator"


def main() -> None:
    resp = requests.get(URL, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    data = resp.json()
    print(f"Count: {len(data)}")
    print("First 3 records:")
    print(json.dumps(data[:3], indent=2))


if __name__ == "__main__":
    main()
