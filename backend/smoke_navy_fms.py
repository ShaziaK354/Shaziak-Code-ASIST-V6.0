# Before
# URL = "http://localhost:3000/api/query/stream"
# r = requests.post(URL, json=payload, headers=headers, timeout=30)

# After (public GET)
import requests, re

URL = "http://localhost:3000/api/samm/workflow"
params = {"q": "Which agency is responsible for Navy FMS cases?"}

r = requests.get(URL, params=params, timeout=30)  # public GET, no auth
r.raise_for_status()
text = r.text.lower()

ok = ("dsca" in text) and ("nipo" in text) and ("dla" not in text)
print("Response snippet:\n", re.sub(r"\s+", " ", text)[:400])
assert ok, "Expected DSCA & NIPO present and DLA absent"
print("✅ Smoke test passed.")
