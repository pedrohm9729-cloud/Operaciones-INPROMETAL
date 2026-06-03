import os
import sys

# Append project path
PROJECT_PATH = r"G:\Mi unidad\AUTOMATIZACIONES\Registro de ventas - Gmail - Coda - Excel"
sys.path.append(PROJECT_PATH)

import gastos_bancarios
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = gastos_bancarios.SPREADSHEET_ID

def main():
    creds = gastos_bancarios.autenticar()
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # 1. Fetch NO IDENTIFICADO
    res_no_id = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="'NO IDENTIFICADO'!A:Q"
    ).execute()
    rows_no_id = res_no_id.get('values', [])
    
    print("=================== NO IDENTIFICADO ===================")
    if len(rows_no_id) <= 1:
        print("No hay filas en NO IDENTIFICADO.")
    else:
        for idx, r in enumerate(rows_no_id[1:], start=2):
            fecha = r[0] if len(r) > 0 else ''
            banco = r[1] if len(r) > 1 else ''
            monto = r[3] if len(r) > 3 else ''
            titular = r[5] if len(r) > 5 else ''
            destinatario = r[6] if len(r) > 6 else ''
            concepto = r[7] if len(r) > 7 else ''
            msg_id = r[13] if len(r) > 13 else ''
            nota = r[14] if len(r) > 14 else ''
            print(f"Fila {idx} | Fecha: {fecha} | Banco: {banco} | Monto: {monto} | Titular: {titular}")
            print(f"  Destinatario: {destinatario} | Concepto: {concepto}")
            print(f"  ID Mensaje: {msg_id}")
            print(f"  Nota/Motivo: {nota}")
            print("-" * 50)
            
    # 2. Fetch REVISAR
    res_rev = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="'REVISAR'!A:J"
    ).execute()
    rows_rev = res_rev.get('values', [])
    
    print("\n=================== REVISAR ===================")
    if len(rows_rev) <= 1:
        print("No hay filas en REVISAR.")
    else:
        for idx, r in enumerate(rows_rev[1:], start=2):
            fecha = r[0] if len(r) > 0 else ''
            banco = r[1] if len(r) > 1 else ''
            empresa = r[2] if len(r) > 2 else ''
            monto = r[3] if len(r) > 3 else ''
            destinatario = r[4] if len(r) > 4 else ''
            concepto = r[5] if len(r) > 5 else ''
            confianza = r[8] if len(r) > 8 else ''
            nota = r[9] if len(r) > 9 else ''
            print(f"Fila {idx} | Fecha: {fecha} | Banco: {banco} | Monto: {monto} | Empresa: {empresa}")
            print(f"  Destinatario: {destinatario} | Concepto: {concepto}")
            print(f"  Confianza: {confianza} | Nota: {nota}")
            print("-" * 50)

if __name__ == '__main__':
    main()
