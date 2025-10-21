import os
from dotenv import load_dotenv
import httpx

load_dotenv()
url = os.getenv('GEMINI_API_URL')
key_present = bool(os.getenv('GEMINI_API_KEY'))
print(f'GEMINI_API_URL present: {bool(url)}; GEMINI_API_KEY present: {key_present}')
if not url:
    print('No GEMINI_API_URL set')
else:
    try:
        print('Sending POST...')
        r = httpx.post(url, json={"input": "Prueba desde bot: saluda y responde breve"}, timeout=15.0)
        print('STATUS', r.status_code)
        print('CONTENT-TYPE', r.headers.get('content-type', ''))
        body = r.text
        if len(body) > 2000:
            print(body[:2000])
            print('\n... (truncated)')
        else:
            print(body)
    except Exception as e:
        print('REQUEST ERROR', repr(e))
