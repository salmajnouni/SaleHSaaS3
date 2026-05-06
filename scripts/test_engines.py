import requests, json, time

QUERY = 'Redis connection refused port 6379'
BASE = 'http://localhost:8888/search'
ENGINES = ['bing', 'google', 'duckduckgo', 'qwant', 'yahoo', 'brave', 'startpage', 'wikipedia', 'github', 'stackoverflow', 'presearch', 'mojeek', 'yandex', 'dogpile', 'ask', 'aol']

for eng in ENGINES:
    try:
        r = requests.get(BASE, params={
            'q': QUERY,
            'format': 'json',
            'language': 'en',
            'engines': eng
        }, timeout=10)
        data = r.json()
        results = data.get('results', [])
        unresp = data.get('unresponsive_engines', [])
        if unresp:
            print(f"  {eng}: UNRESPONSIVE - {unresp}")
        elif results:
            first = results[0].get('title', '')[:60]
            relevant = any(kw in first.lower() for kw in ['redis', 'connect', 'refused', 'port', 'error', 'stack'])
            tag = 'RELEVANT' if relevant else 'IRRELEVANT'
            print(f"  {eng}: {len(results)} results [{tag}] - {first}")
        else:
            print(f"  {eng}: 0 results")
    except Exception as e:
        print(f"  {eng}: ERROR - {str(e)[:50]}")
    time.sleep(0.5)
