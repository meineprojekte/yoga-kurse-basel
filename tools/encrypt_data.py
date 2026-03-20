#!/usr/bin/env python3
"""
Encrypts JSON data files using simple reversible encoding.
The encoding rotates each byte by a fixed offset, then base64 encodes.
Matching decode logic is in app.js.
"""
import json, os, base64

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
ROTATE = 47  # Same value used in JS decoder

def encode(data_str):
    raw = data_str.encode('utf-8')
    rotated = bytes((b + ROTATE) % 256 for b in raw)
    return base64.b64encode(rotated).decode('ascii')

def main():
    count = 0
    for f in sorted(os.listdir(DATA_DIR)):
        if (f.startswith('studios_') or f.startswith('schedule_')) and f.endswith('.json') and '.enc.' not in f:
            path = os.path.join(DATA_DIR, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            try:
                json.loads(content)
            except json.JSONDecodeError:
                print(f'  SKIP: {f}')
                continue
            enc = encode(content)
            enc_path = path.replace('.json', '.enc.json')
            with open(enc_path, 'w') as fh:
                json.dump({'v': 2, 'd': enc}, fh)
            print(f'  OK: {f}')
            count += 1
    print(f'Encrypted {count} files')

if __name__ == '__main__':
    main()
