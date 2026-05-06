import requests, json

# Test SearXNG directly from host
r = requests.get('http://localhost:8888/search', params={
    'q': 'ConnectionRefusedError Redis port 6379',
    'format': 'json',
    'language': 'en',
    'engines': 'bing,github'
}, timeout=15)
print('Status:', r.status_code)
data = r.json()
results = data.get('results', [])
print('Results:', len(results))
for i, res in enumerate(results[:5], 1):
    eng = res.get('engine', '?')
    title = res.get('title', '?')[:80]
    url = res.get('url', '')
    print(f"  {i}. [{eng}] {title}")
    print(f"     {url}")

print()
print('Unresponsive:', data.get('unresponsive_engines', []))

# Try with site:stackoverflow
print()
print('--- With site:stackoverflow.com ---')
r2 = requests.get('http://localhost:8888/search', params={
    'q': 'ConnectionRefusedError Redis port 6379 site:stackoverflow.com',
    'format': 'json',
    'language': 'en',
    'engines': 'bing'
}, timeout=15)
d2 = r2.json()
res2 = d2.get('results', [])
print('Results:', len(res2))
for i, res in enumerate(res2[:5], 1):
    title = res.get('title', '?')[:80]
    url = res.get('url', '')
    print(f"  {i}. {title}")
    print(f"     {url}")

# Try mojeek
print()
print('--- mojeek ---')
r3 = requests.get('http://localhost:8888/search', params={
    'q': 'Redis connection refused 6379',
    'format': 'json',
    'language': 'en',
    'engines': 'mojeek'
}, timeout=15)
d3 = r3.json()
res3 = d3.get('results', [])
print('Results:', len(res3))
for i, res in enumerate(res3[:3], 1):
    print(f"  {i}. {res.get('title', '?')[:80]}")
print('Unresponsive:', d3.get('unresponsive_engines', []))
