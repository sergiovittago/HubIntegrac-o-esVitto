from flask import request, jsonify, make_response
from config import STRIPE_SECRET_KEY, GOOGLE_CREDENTIALS_BASE64, SPREADSHEET_ID
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import base64
from utils.slack import enviar_log_slack

cred_dict = json.loads(base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8"))
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_info(cred_dict, scopes=SCOPES)
client = gspread.authorize(CREDS)
sheet = client.open_by_key(SPREADSHEET_ID)
worksheet = sheet.worksheet("PESSOA FISICA")

def stripe_webhook():
    try:
        payload = request.get_json()
        print("📡 [Stripe] Webhook recebido:")
        print(json.dumps(payload, indent=2))

        if payload.get("acao") == "cancelar_assinatura":
            subscription_id = payload.get("subscription_id", "").strip()
            if not subscription_id:
                enviar_log_slack("❌ [Stripe] subscription_id ausente no payload.", sucesso=False)
                return make_response("subscription_id ausente", 400)
            response = requests.delete(
                f"https://api.stripe.com/v1/subscriptions/{subscription_id}",
                auth=(STRIPE_SECRET_KEY, "")
            )
            if response.status_code == 200:
                enviar_log_slack(f"✅ [Stripe] Assinatura cancelada: {subscription_id}", sucesso=True)
                return jsonify({"status": "assinatura cancelada"}), 200
            else:
                enviar_log_slack(f"❌ [Stripe] Falha ao cancelar assinatura: {response.text}", sucesso=False)
                return make_response("Erro ao cancelar", 500)

        # Evento normal de pagamento
        data = payload.get("data", {}).get("object", {})
        cpf = data.get("client_reference_id")
        status = data.get("payment_status") or "desconhecido"
        assinatura_id = data.get("subscription")

        if not cpf:
            enviar_log_slack("⚠️ [Stripe] CPF ausente no payload.", sucesso=False)
            return make_response("CPF ausente no payload", 400)

        print(f"🔍 [Stripe] Atualizando: CPF={cpf} | Status={status} | Assinatura={assinatura_id}")

        # Localiza linha do CPF na planilha
        try:
            celula = worksheet.find(cpf)
            linha = celula.row
            worksheet.update_cell(linha, 13, status)  # Coluna M: STATUS PAGAMENTO
            worksheet.update_cell(linha, 14, assinatura_id or "-")  # Coluna N: ID ASSINATURA
            enviar_log_slack(f"✅ [Stripe] Pagamento atualizado com sucesso para {cpf}", sucesso=True)
            return jsonify({"status": "ok"}), 200
        except gspread.exceptions.CellNotFound:
            enviar_log_slack(f"❌ [Stripe] CPF não encontrado: {cpf}", sucesso=False)
            return make_response("CPF não encontrado", 404)

    except Exception as e:
        msg = f"🔥 [Stripe] Erro interno inesperado: {e}"
        print(msg)
        enviar_log_slack(msg, sucesso=False)
        return make_response("Erro interno", 500)