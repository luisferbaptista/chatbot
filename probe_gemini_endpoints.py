import os
from dotenv import load_dotenv
import httpx

load_dotenv()
API_KEY = os.getenv('GEMINI_API_KEY')
API_URL = os.getenv('GEMINI_API_URL')

if not API_KEY:
    print('No GEMINI_API_KEY in .env')
    raise SystemExit(1)

candidates = [
    # (puntos finales de lenguaje generativo comunes)
    ('v1 text-bison', f'https://generativelanguage.googleapis.com/v1/models/text-bison-001:generate'),
    ('v1 gemini-pro generate', f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generate'),
    ('v1 gemini-pro generateContent', f'https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent'),
    ('v1beta gemini-pro generateContent', f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'),
    ('v1beta2 gemini-pro generate', f'https://generativelanguage.googleapis.com/v1beta2/models/gemini-pro:generate'),
    ('v1beta2 text-bison', f'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate'),
]

payloads = [
    ('prompt_text', {"prompt": {"text": "Hola, responde breve."}}),
    ('input_simple', {"input": "Hola, responde breve."}),
    ('instances_vertex', {"instances": [{"content": "Hola, responde breve."}]}),
]

headers = {"Content-Type": "application/json"}

print('Using API key from .env (will not print it).')
print('Also checking the GEMINI_API_URL from .env (masked):', ('(present)' if API_URL else '(not set)'))

results = []

with httpx.Client(timeout=15.0) as client:
    for name, base in candidates:
        for p_name, payload in payloads:
            # adjuntar key como parámetro de consulta
            url = base
            sep = '&' if '?' in url else '?'
            url_with_key = f"{url}{sep}key={API_KEY}"
            try:
                r = client.post(url_with_key, json=payload, headers=headers)
                status = r.status_code
                text = r.text
            except Exception as e:
                status = None
                text = f'EXCEPTION: {e!r}'

            # enmascarar la key cuando se imprime la URL
            masked_url = url_with_key
            if 'key=' in masked_url:
                masked_url = masked_url.split('key=')[0] + 'key=***'

            summary = {
                'endpoint_name': name,
                'payload_name': p_name,
                'url': masked_url,
                'status': status,
                'body_snippet': (text[:2000] + '...') if text and len(text) > 2000 else (text or ''),
            }
            results.append(summary)
            print('---')
            print('Endpoint:', name, 'Payload:', p_name)
            print('URL:', masked_url)
            print('Status:', status)
            print('Body snippet:', summary['body_snippet'])

print('\nDone. Summary:')
for r in results:
    print(r['endpoint_name'], r['payload_name'], '->', r['status'])
