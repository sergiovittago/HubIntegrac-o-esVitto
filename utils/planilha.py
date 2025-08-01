import gspread
from google.oauth2.service_account import Credentials
from config import cred_dict, SPREADSHEET_ID, SHEET_NAME

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_info(cred_dict, scopes=SCOPES)
client = gspread.authorize(CREDS)
sheet = client.open_by_key(SPREADSHEET_ID)
worksheet = sheet.worksheet(SHEET_NAME)

def atualizar_status_pagamento(cpf, status, assinatura_id=None):
    all_rows = worksheet.get_all_values()
    header = all_rows[0]

    col_cpf = 2  # Coluna B
    col_status = header.index("STATUS LINK PAGAMENTO") + 1
    col_status_final = 8  # Coluna H
    col_assinatura = header.index("ID ASSINATURA") + 1

    cpf = cpf.strip().zfill(11)

    for i, row in enumerate(all_rows[1:], start=2):
        cpf_planilha = row[col_cpf - 1].strip().zfill(11)
        if cpf_planilha == cpf:
            worksheet.update_cell(i, col_status, status)
            if status.lower() == "paid":
                worksheet.update_cell(i, col_status_final, "LIBERAÇÃO")
                if assinatura_id:
                    worksheet.update_cell(i, col_assinatura, assinatura_id)
            return True
    return False