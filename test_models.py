import os
import sys
import json
import urllib.request
import urllib.error

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios

def test_model(model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key=" + gastos_bancarios.GEMINI_API_KEY
    print(f"\n--- Testing Model: {model_name} ---")
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 2048,
            'responseMimeType': 'application/json'
        }
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            url, data=body,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
            text = raw['candidates'][0]['content']['parts'][0]['text']
            finish_reason = raw['candidates'][0].get('finishReason', 'UNKNOWN')
            usage = raw.get('usageMetadata', {})
            print(f"Success! Finish Reason: {finish_reason}")
            print(f"Usage: {usage}")
            print("Response:")
            print(text.strip())
            return True
    except Exception as e:
        print(f"Error for {model_name}: {e}")
        return False

def main():
    prompt = "Responde con un JSON simple: {'saludo': 'hola desde BCP'}"
    models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-3.5-flash']
    for m in models:
        test_model(m, prompt)

if __name__ == '__main__':
    main()
