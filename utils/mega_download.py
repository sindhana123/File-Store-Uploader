import base64
import json
import re
import os
import struct
import aiohttp
import asyncio
from Crypto.Cipher import AES
from Crypto.Util import Counter

def parse_mega_url(url: str):
    url = url.replace(' ', '')
    # V2 URL structure: https://mega.nz/file/3Qk3GCYC#4LG1IluxtxT3NWkKdYcQFR7oRdO-4EMdIE1d-KzQVDs
    if '/file/' in url:
        part = url.split('/file/')[1]
        if '#' in part:
            file_id, file_key = part.split('#', 1)
            return file_id, file_key
    # V1 URL structure: https://mega.nz/#!3Qk3GCYC!4LG1IluxtxT3NWkKdYcQFR7oRdO-4EMdIE1d-KzQVDs
    elif '#!' in url:
        part = url.split('#!')[1]
        if '!' in part:
            file_id, file_key = part.split('!', 1)
            return file_id, file_key
    raise ValueError("Invalid Mega.nz URL format")

def base64_url_decode(data: str) -> bytes:
    data += '=='[(2 - len(data) * 3) % 4:]
    for search, replace in (('-', '+'), ('_', '/'), (',', '')):
        data = data.replace(search, replace)
    return base64.b64decode(data)

def base64_to_a32(s: str):
    return str_to_a32(base64_url_decode(s))

def str_to_a32(b):
    if isinstance(b, str):
        b = b.encode('latin-1')
    if len(b) % 4:
        b += b'\0' * (4 - len(b) % 4)
    return struct.unpack('>%dI' % (len(b) / 4), b)

def a32_to_str(a):
    return struct.pack('>%dI' % len(a), *a)

def aes_cbc_decrypt(data, key):
    aes_cipher = AES.new(key, AES.MODE_CBC, b'\0' * 16)
    return aes_cipher.decrypt(data)

def aes_cbc_decrypt_a32(data, key):
    return str_to_a32(aes_cbc_decrypt(a32_to_str(data), a32_to_str(key)))

def decrypt_key(a, key):
    return sum((aes_cbc_decrypt_a32(a[i:i + 4], key)
                for i in range(0, len(a), 4)), ())

def decrypt_attr(attr, key):
    attr = aes_cbc_decrypt(attr, a32_to_str(key))
    attr = attr.rstrip(b'\0')
    try:
        attr_dec = attr.decode('utf-8', errors='ignore')
        if attr_dec.startswith('MEGA{"'):
            return json.loads(attr_dec[4:])
    except Exception:
        pass
    return False

async def get_mega_file_info(url: str):
    file_id, file_key_str = parse_mega_url(url)
    file_key = base64_to_a32(file_key_str)
    
    payload = [{'a': 'g', 'g': 1, 'p': file_id}]
    
    async with aiohttp.ClientSession() as session:
        api_url = "https://g.api.mega.co.nz/cs?id=0"
        async with session.post(api_url, data=json.dumps(payload), timeout=20) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Mega API request failed with status {resp.status}")
            resp_text = await resp.text()
            json_resp = json.loads(resp_text)
            
            if isinstance(json_resp, list) and len(json_resp) > 0:
                file_data = json_resp[0]
            else:
                file_data = json_resp
                
            if isinstance(file_data, int):
                raise RuntimeError(f"Mega API returned error: {file_data}")
                
            if 'g' not in file_data:
                raise RuntimeError("File not accessible or deleted")
                
            # Decrypt key: k = key[0]^key[4], key[1]^key[5], key[2]^key[6], key[3]^key[7]
            k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
                 file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
            
            attribs_enc = base64_url_decode(file_data['at'])
            attribs = decrypt_attr(attribs_enc, k)
            if not attribs or 'n' not in attribs:
                raise ValueError("Failed to decrypt Mega file attributes")
                
            return {
                'name': attribs['n'],
                'size': file_data['s'],
                'download_url': file_data['g'],
                'key': k,
                'iv': file_key[4:6] + (0, 0),
                'meta_mac': file_key[6:8]
            }

async def download_mega_file(url: str, output_path: str, progress_callback=None):
    info = await get_mega_file_info(url)
    
    file_url = info['download_url']
    file_size = info['size']
    k = info['key']
    iv = info['iv']
    
    k_str = a32_to_str(k)
    counter = Counter.new(128, initial_value=((iv[0] << 32) + iv[1]) << 64)
    aes = AES.new(k_str, AES.MODE_CTR, counter=counter)
    
    downloaded = 0
    
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url, timeout=None) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to fetch Mega file stream: HTTP {resp.status}")
                
            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(128 * 1024):
                    if not chunk:
                        continue
                    decrypted_chunk = aes.decrypt(chunk)
                    f.write(decrypted_chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        await progress_callback(downloaded, file_size)
                        
    return output_path
