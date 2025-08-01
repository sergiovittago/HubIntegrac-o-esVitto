from flask import request, jsonify, make_response
import requests
from config import CLICK_AUTH_TOKEN, CLICK_EMPRESA_ID, CLICK_PLANO_ID, GOOGLE_CREDENTIALS_BASE64, SPREADSHEET_ID
from utils.slack import enviar_log_slack
import gspread
from google.oauth2.service_account import Credentials
import base64
import json

cred_dict = json.loads(base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8"))
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_info(cred_dict, scopes=SCOPES)
client = gspread.authorize(CREDS)
sheet = client.open_by_key(SPREADSHEET_ID)
worksheet = sheet.worksheet("PESSOA FISICA")

def registrar_usuario_clicklife():
    try:
        data = request.get_json()
        cpf = data.get("cpf")
        nome = data.get("nome")
        email = data.get("email")
        senha = data.get("senha")
        datanascimento = data.get("datanascimento")
        sexo = data.get("sexo")
        telefone = data.get("telefone")

        print(f"\U0001F4E5 [ClickLife] Dados recebidos: CPF={cpf} | Nome={nome} | Email={email}")

        if not cpf or not nome or not email:
            print("❌ [ClickLife] CPF, Nome ou Email ausente.")
            enviar_log_slack("❌ [ClickLife] CPF, Nome ou Email ausente no payload.", sucesso=False)
            return make_response("CPF, Nome e Email são obrigatórios", 400)

        url_criar = "https://api.clicklifesaude.com/usuarios"
        payload_criar = {
            "authtoken": CLICK_AUTH_TOKEN,
            "nome": nome,
            "cpf": cpf,
            "email": email,
            "senha": senha,
            "datanascimento": datanascimento,
            "sexo": sexo,
            "telefone": telefone,
            "logradouro": "Antonio Raposo",
            "numero": "186",
            "complemento": "Sala 14",
            "bairro": "Lapa",
            "cep": "05074020",
            "cidade": "Sao Paulo",
            "estado": "SP",
            "empresaid": int(CLICK_EMPRESA_ID),
            "planoid": int(CLICK_PLANO_ID)
        }
        print(f"\U0001F680 [ClickLife] Enviando criação: {payload_criar}")
        r1 = requests.post(url_criar, json=payload_criar)
        print(f"\U0001F4EC [ClickLife] Resposta criação: {r1.status_code} - {r1.text}")

        if r1.status_code != 200:
            mensagem = f"❌ [ClickLife] Falha ao criar usuário:\nCPF: {cpf}\nErro: {r1.text}"
            enviar_log_slack(mensagem, sucesso=False)
            return make_response(f"Erro na criação: {r1.text}", 500)

        url_ativar = "https://api.clicklifesaude.com/usuarios/ativacao"
        payload_ativar = {
            "authtoken": CLICK_AUTH_TOKEN,
            "cpf": cpf,
            "empresaid": CLICK_EMPRESA_ID,
            "planoid": CLICK_PLANO_ID,
            "proposito": "Ativar"
        }
        print(f"\U0001F680 [ClickLife] Enviando ativação: {payload_ativar}")
        r2 = requests.post(url_ativar, json=payload_ativar)
        print(f"\U0001F4EC [ClickLife] Resposta ativação: {r2.status_code} - {r2.text}")

        if r2.status_code != 200:
            mensagem = f"❌ [ClickLife] Falha ao ativar usuário:\nCPF: {cpf}\nErro: {r2.text}"
            enviar_log_slack(mensagem, sucesso=False)
            return make_response(f"Erro na ativação: {r2.text}", 500)

        mensagem = f"✅ [ClickLife] Usuário criado e ativado com sucesso:\nCPF: {cpf}\nNome: {nome}"
        enviar_log_slack(mensagem, sucesso=True)

        return jsonify({"status": "usuário criado e ativado", "cpf": cpf}), 200

    except Exception as e:
        msg = f"\U0001F525 [ClickLife] Erro inesperado: {str(e)}"
        print(msg)
        enviar_log_slack(msg, sucesso=False)
        return make_response(f"Erro interno: {e}", 500)