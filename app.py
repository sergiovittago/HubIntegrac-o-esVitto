from flask import Flask
from stripe_integ.webhook import stripe_webhook
from clicklife.registrar import registrar_usuario_clicklife

app = Flask(__name__)

# === Rotas principais ===
app.add_url_rule("/webhook-stripe", view_func=stripe_webhook, methods=["POST"])
app.add_url_rule("/clicklife/registrar", view_func=registrar_usuario_clicklife, methods=["POST"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)