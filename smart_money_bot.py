import telebot
from flask import Flask, request
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

# Configuration du Flask pour recevoir les Webhooks
app = Flask(__name__)

# Commande de base pour tester ton bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Bienvenue dans ton bot connecté à TradingView !")

# Route Webhook pour recevoir les alertes de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        symbol = data.get("symbol", "Inconnu")
        price = data.get("price", "Inconnu")
        signal = data.get("signal", "Aucun signal")

        message = (
            f"📊 **Signal TradingView**\n"
            f"💹 Actif : {symbol}\n"
            f"💰 Prix : {price}\n"
            f"🚨 Signal : {signal}"
        )

        bot.send_message(-100123456789, message)  # Remplace par ton ID de chat Telegram

        return {"status": "success", "message": "Signal envoyé avec succès."}

    except Exception as e:
        print(f"Erreur : {e}")
        return {"status": "error", "message": str(e)}

# Lancement du bot et du serveur Flask
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: bot.polling()).start()
    app.run(host="0.0.0.0", port=5000)
