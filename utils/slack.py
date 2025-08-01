import requests

# Webhooks do Slack
SLACK_WEBHOOK_SUCESSO = "https://hooks.slack.com/services/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"
SLACK_WEBHOOK_ERRO = "https://hooks.slack.com/services/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"

def enviar_log_slack(mensagem, sucesso=True):
    webhook_url = SLACK_WEBHOOK_SUCESSO if sucesso else SLACK_WEBHOOK_ERRO
    payload = {"text": mensagem}
    try:
        response = requests.post(webhook_url, json=payload)
        print(f"📤 Slack log enviado ({'sucesso' if sucesso else 'erro'}): {response.status_code}")
    except Exception as e:
        print(f"❌ Falha ao enviar log para Slack: {e}")