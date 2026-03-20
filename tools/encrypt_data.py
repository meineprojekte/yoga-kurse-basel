#!/usr/bin/env python3
"""
Encrypts all JSON data files so they cannot be read without the decryption key.
The key is embedded in the JavaScript and split into parts to make it harder to find.
Uses XOR-based encryption with a rotating key - simple but effective for obfuscation.
"""

import json
import os
import base64
import hashlib

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# Encryption key - derived from multiple parts (same as in JS)
KEY_PARTS = ['yoga', 'schweiz', '2026', 'protect']
KEY = hashlib.sha256(''.join(KEY_PARTS).encode()).hexdigest()


def xor_encrypt(data_str, key):
    """XOR encrypt a string with a repeating key."""
    key_bytes = key.encode('utf-8')
    data_bytes = data_str.encode('utf-8')
    encrypted = bytearray(len(data_bytes))
    for i in range(len(data_bytes)):
        encrypted[i] = data_bytes[i] ^ key_bytes[i % len(key_bytes)]
    return base64.b64encode(encrypted).decode('utf-8')


def process_file(filepath):
    """Encrypt a JSON file and save as .enc.json"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Validate it's proper JSON
    try:
        json.loads(content)
    except json.JSONDecodeError:
        # Might already be encrypted
        print(f'  SKIP (not valid JSON): {os.path.basename(filepath)}')
        return False

    encrypted = xor_encrypt(content, KEY)

    # Write encrypted version
    enc_path = filepath.replace('.json', '.enc.json')
    with open(enc_path, 'w', encoding='utf-8') as f:
        json.dump({'v': 1, 'd': encrypted}, f)

    print(f'  OK: {os.path.basename(filepath)} -> {os.path.basename(enc_path)}')
    return True


def main():
    print('Encrypting data files...')
    print(f'Key hash: {KEY[:16]}...')

    count = 0
    for filename in sorted(os.listdir(DATA_DIR)):
        if filename.startswith('studios_') and filename.endswith('.json') and '.enc.' not in filename:
            if process_file(os.path.join(DATA_DIR, filename)):
                count += 1
        elif filename.startswith('schedule_') and filename.endswith('.json') and '.enc.' not in filename:
            if process_file(os.path.join(DATA_DIR, filename)):
                count += 1

    print(f'\nEncrypted {count} files.')
    print('Remember to update app.js to load .enc.json files!')


if __name__ == '__main__':
    main()
