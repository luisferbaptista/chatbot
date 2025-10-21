import os
from dotenv import load_dotenv
import httpx

load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print('GEMINI_API_KEY present:', bool(key))
url = f'https://generativelanguage.googleapis.com/v1/models/text-bison-001:generate?key={key}'
print('URL:', url[:100] + ('...' if len(url)>100 else ''))
try:
    r = httpx.post(url, json={"prompt": {"text": "Hola, prueba corta desde text-bison-001"}}, timeout=15.0)
    print('STATUS', r.status_code)
    print(r.text[:2000])
except Exception as e:
    print('ERROR', repr(e))
