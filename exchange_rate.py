import json
import os
import time

import requests

import config


_cached_rate = None
_last_fetch_time = 0
_CACHE_DURATION_SECONDS = 3600


def get_bdt_to_usd_rate() -> float:
    global _cached_rate, _last_fetch_time

    now = time.time()
    if _cached_rate is None or (now - _last_fetch_time) > _CACHE_DURATION_SECONDS:
        response = requests.get('https://open.er-api.com/v6/latest/BDT', timeout=5)
        data = response.json()
        with open('rate.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

        if data['result'] == 'success':
            _cached_rate = data['rates']['USD']
            _last_fetch_time = now
        elif _cached_rate is None:
            raise Exception('Failed to fetch exchange rate and no cache available')
        else:
            print('Warning: using cached rate, API call failed')

    return _cached_rate

def get_rate_with_fallback() -> float:
    try:
        rate = get_bdt_to_usd_rate()
        with open(config.RATE_FALLBACK_FILE, 'w', encoding='utf-8') as file:
            json.dump({'rate': rate, 'timestamp': time.time()}, file)
        return rate
    except (requests.exceptions.RequestException, KeyError):
        if os.path.exists(config.RATE_FALLBACK_FILE):
            with open(config.RATE_FALLBACK_FILE, 'r') as file:
                saved = json.load(file)
                return saved['rate']
        else:
            raise Exception('No internet and no save rate available')