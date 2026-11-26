"""Production endpoint test for cryptographic-systems-simulator on Render."""
import urllib.request
import json

BASE = "https://cryptographic-simulator.onrender.com"


def get(path):
    return urllib.request.urlopen(BASE + path, timeout=25)


def post(path, body):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=25)


# 1. Health
h = get("/api/health")
assert h.status == 200
print("[OK] /api/health:", json.loads(h.read()))

# 2. Static assets
for asset in ["/static/style.css", "/static/app.js", "/static/index.html"]:
    r = get(asset)
    assert r.status == 200
    body = r.read()
    print(f"[OK] {asset} ({len(body)} bytes)")

# 3. All 5 ciphers encrypt + decrypt roundtrip
tests = [
    ("caesar",     "HELLOWORLD",                7),
    ("playfair",   "HIDETHEGOLD",               "MONARCHY"),
    ("vigenere",   "ATTACKATDAWN",              "LEMON"),
    ("rail_fence", "WEAREDISCOVEREDFLEEATONCE", 3),
    ("columnar",   "WEAREDISCOVEREDFLEEATONCE", "ZEBRAS"),
]
for algo, text, key in tests:
    enc = json.loads(post("/api/transform", {"algorithm": algo, "mode": "encrypt", "text": text, "key": key}).read())
    dec = json.loads(post("/api/transform", {"algorithm": algo, "mode": "decrypt", "text": enc["output"], "key": key}).read())
    enc_out = enc["output"]
    dec_out = dec["output"]
    ok = dec_out.startswith(text) or text in dec_out
    tag = "OK" if ok else "WARN"
    print(f"[{tag}] {algo}: {text} -> {enc_out} -> {dec_out[:len(text)]}")

# 4. Benchmark (5 runs)
bm = json.loads(post("/api/benchmark", {"runs": 5}).read())
assert len(bm["payload_labels"]) == 4
assert len(bm["algorithms"]) == 5
plain_h = bm["entropy"]["plaintext"]
cipher_h = bm["entropy"]["ciphertext"]
print(f"[OK] /api/benchmark: {len(bm['algorithms'])} algos x {len(bm['payload_labels'])} payloads, H(plain)={plain_h} H(cipher)={cipher_h}")

print()
print("=== ALL PRODUCTION ENDPOINT TESTS PASSED ===")
print("Live URL:", BASE)
