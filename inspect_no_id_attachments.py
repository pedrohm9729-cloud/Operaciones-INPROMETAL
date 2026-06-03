import os
import sys
import base64

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def inspect_msg(service, msg_id):
    print(f"\n================ INSPECTING MSG: {msg_id} ================")
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg['payload'].get('headers', [])
    to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), 'None')
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'None')
    print(f"Subject: {subject}")
    print(f"To: {to_header}")
    
    # Check fallback / XML
    texto = gastos_bancarios.obtener_texto(msg)
    emp_fallback, _ = gastos_bancarios.detectar_titular_fallback(texto, '')
    print(f"Fallback detection: {emp_fallback}")
    
    att_id = gastos_bancarios.obtener_xml_attachment_id(service, msg)
    if att_id:
        print(f"Found XML attachment ID: {att_id}")
        att = service.users().messages().attachments().get(
            userId='me', messageId=msg_id, id=att_id
        ).execute()
        data = att.get('data', '')
        if data:
            xml_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            reg_name = gastos_bancarios.obtener_titular_de_xml(xml_text)
            print(f"XML Client Registration Name: '{reg_name}'")
            if reg_name:
                emp_xml, _ = gastos_bancarios.detectar_titular_fallback(reg_name, '')
                print(f"XML Client matched: {emp_xml}")
    else:
        print("No XML attachment found.")

def main():
    creds = gastos_bancarios.autenticar()
    service = build('gmail', 'v1', credentials=creds)
    inspect_msg(service, '19c3a1be947423c5')
    inspect_msg(service, '19cc6069e15133c4')

if __name__ == '__main__':
    main()
