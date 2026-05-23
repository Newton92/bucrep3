import json
# Read raw bytes to verify
with open('scripts/naf_extracted.json', 'rb') as f:
    raw = f.read(500)

# Check if it's valid UTF-8
try:
    text = raw.decode('utf-8')
    print("UTF-8 OK. Sample:")
    print(text[:300])
except UnicodeDecodeError as e:
    print(f"UTF-8 error: {e}")
    # Try cp1252
    try:
        text = raw.decode('cp1252')
        print("CP1252 OK. Sample:")
        print(text[:200])
    except Exception as e2:
        print(f"CP1252 error: {e2}")
