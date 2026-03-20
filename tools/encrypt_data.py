#!/usr/bin/env python3
"""Encrypt JSON data: base64 encode then reverse. Simple but effective obfuscation."""
import json, os, base64

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

def encrypt(json_str):
    b64 = base64.b64encode(json_str.encode('utf-8')).decode('ascii')
    return b64[::-1]  # reverse

def main():
    count = 0
    for f in sorted(os.listdir(DATA_DIR)):
        if (f.startswith('studios_') or f.startswith('schedule_')) and f.endswith('.json') and '.enc.' not in f:
            path = os.path.join(DATA_DIR, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            try:
                json.loads(content)
            except:
                continue
            enc = encrypt(content)
            enc_path = path.replace('.json', '.enc.json')
            with open(enc_path, 'w') as fh:
                json.dump({'e': enc}, fh)
            count += 1
            print(f'  OK: {f}')
    print(f'\nEncrypted {count} files')

if __name__ == '__main__':
    main()
