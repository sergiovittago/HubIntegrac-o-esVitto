from flask import request, jsonify, make_response
import requests
from config import CLICK_AUTH_TOKEN, CLICK_EMPRESA_ID, CLICK_PLANO_ID
from utils.slack import enviar_log_slack

def registrar_usuario_clicklife():
    try:
        data = request.get_json()
        cpf = data.get("cpf")
        nome = data.get("nome")
        email = data.get("email")
        telefone = data.get("telefone")

        print(f"📥 [ClickLife] Dados recebidos: CPF={cpf} | Nome={nome} | Email={email} | Tel={telefone}")

        if not cpf or not nome:
            print("❌ [ClickLife] CPF ou Nome ausente.")
            enviar_log_slack("❌ [ClickLife] CPF ou nome ausente no payload.", sucesso=False)
            return make_response("CPF e nome são obrigatórios", 400)

        url_criar = "https://api.clicklifesaude.com/usuarios"
        payload_criar = {
            "authtoken": CLICK_AUTH_TOKEN,
            "nome": nome,
            "cpf": cpf,
            "email": email,
            "telefone": telefone,
            "empresaid": CLICK_EMPRESA_ID
        }
        print(f"🚀 [ClickLife] Enviando criação: {payload_criar}")
        r1 = requests.post(url_criar, json=payload_criar)
        print(f"📬 [ClickLife] Resposta criação: {r1.status_code} - {r1.text}")

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
        print(f"🚀 [ClickLife] Enviando ativação: {payload_ativar}")
        r2 = requests.post(url_ativar, json=payload_ativar)
        print(f"📬 [ClickLife] Resposta ativação: {r2.status_code} - {r2.text}")

        if r2.status_code != 200:
            mensagem = f"❌ [ClickLife] Falha ao ativar usuário:\nCPF: {cpf}\nErro: {r2.text}"
            enviar_log_slack(mensagem, sucesso=False)
            return make_response(f"Erro na ativação: {r2.text}", 500)

        mensagem = f"✅ [ClickLife] Usuário criado e ativado com sucesso:\nCPF: {cpf}\nNome: {nome}"
        enviar_log_slack(mensagem, sucesso=True)

        return jsonify({"status": "usuário criado e ativado", "cpf": cpf}), 200

    except Exception as e:
        msg = f"🔥 [ClickLife] Erro inesperado: {str(e)}"
        print(msg)
        enviar_log_slack(msg, sucesso=False)
        return make_response(f"Erro interno: {e}", 500)