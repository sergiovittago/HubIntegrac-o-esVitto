from flask import request, jsonify, make_response
from config import STRIPE_SECRET_KEY
import requests
import json
from utils.planilha import atualizar_status_pagamento
from utils.slack import enviar_log_slack

def stripe_webhook():
    try:
        payload = request.get_json()
        print("📡 [Stripe] Webhook recebido:")
        print(json.dumps(payload, indent=2))

        if payload.get("acao") == "cancelar_assinatura":
            subscription_id = payload.get("subscription_id", "").strip()
            print(f"🛑 [Stripe] Requisição de cancelamento recebida | Subscription ID: {subscription_id}")

            if not subscription_id:
                print("❌ [Stripe] subscription_id ausente")
                enviar_log_slack("❌ [Stripe] subscription_id ausente no payload.", sucesso=False)
                return make_response("subscription_id ausente", 400)

            try:
                response = requests.delete(
                    f"https://api.stripe.com/v1/subscriptions/{subscription_id}",
                    auth=(STRIPE_SECRET_KEY, "")
                )
                print(f"📬 [Stripe] Resposta do cancelamento: {response.status_code} - {response.text}")

                if response.status_code == 200:
                    msg = f"✅ [Stripe] Assinatura cancelada: {subscription_id}"
                    enviar_log_slack(msg, sucesso=True)
                    return jsonify({"status": "assinatura cancelada"}), 200
                else:
                    msg = f"❌ [Stripe] Falha ao cancelar assinatura: {subscription_id}\nErro: {response.text}"
                    enviar_log_slack(msg, sucesso=False)
                    return make_response("Erro ao cancelar", 500)
            except Exception as e:
                msg = f"🔥 [Stripe] Erro interno no cancelamento: {str(e)}"
                print(msg)
                enviar_log_slack(msg, sucesso=False)
                return make_response("Erro interno", 500)

        # Evento normal do Stripe
        event_type = payload.get("type")
        data = payload.get("data", {}).get("object", {})
        cpf = data.get("client_reference_id")
        status = data.get("payment_status") or "desconhecido"
        assinatura_id = data.get("subscription")

        print(f"📄 [Stripe] Evento recebido: {event_type}")
        print(f"🔎 [Stripe] Extraído: CPF={cpf} | Status={status} | Assinatura={assinatura_id}")

        if not cpf:
            print("⚠️ [Stripe] CPF ausente no payload.")
            enviar_log_slack("⚠️ [Stripe] CPF ausente no payload.", sucesso=False)
            return make_response("CPF ausente no payload", 400)

        sucesso = atualizar_status_pagamento(cpf, status, assinatura_id)

        if sucesso:
            msg = f"✅ [Stripe] Pagamento atualizado com sucesso:\nCPF: {cpf}\nStatus: {status}"
            enviar_log_slack(msg, sucesso=True)
            return jsonify({"status": "ok"}), 200
        else:
            msg = f"❌ [Stripe] CPF não encontrado na planilha:\nCPF: {cpf}"
            enviar_log_slack(msg, sucesso=False)
            return make_response("CPF não encontrado", 404)

    except Exception as e:
        msg = f"🔥 [Stripe] Erro interno inesperado: {e}"
        print(msg)
        enviar_log_slack(msg, sucesso=False)
        return make_response("Erro interno", 500)