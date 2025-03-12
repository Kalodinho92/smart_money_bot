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

# Gestion du Risk/Reward 1:5 avec SL précis (10 pips pour Forex, 20 pips pour US30)
def calculate_sl_tp(entry_price, symbol, rr_ratio=5):
    if "USD" in symbol and symbol != "US30":
        stop_loss = entry_price - 0.0010  # 10 pips pour Forex
    elif symbol == "US30":
        stop_loss = entry_price - 2.0  # 20 pips pour US30
    else:
        stop_loss = entry_price * 0.98  # Par défaut, SL à 2% sous le prix d'entrée

    take_profit = entry_price + (entry_price - stop_loss) * rr_ratio
    return stop_loss, take_profit

# Fonction pour valider les confirmations et gérer les signaux
def validate_trade(confirmations):
    return len(confirmations) >= 5, confirmations

# Webhook pour gérer les signaux de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    # Vérifie si les données sont bien envoyées en JSON
    if request.headers['Content-Type'] != 'application/json':
        return {"status": "error", "message": "Format de données non supporté"}, 415

    data = request.json  # Lecture correcte des données JSON

    symbol = data.get("symbol", "Inconnu")
    entry_price = float(data.get("price", 0))

    # Identification automatique d'une alerte "Auto Fib Extension"
    if "Fib" in symbol or "Extension" in symbol:
        confirmation = "Fibonacci FVG"
    else:
        confirmation = data.get("confirmation", "")

    # Gestion des confirmations
    valid_confirmations = []

    if confirmation in [
        "Pivot Point", "Session High/Low", "Fibonacci FVG", 
        "Order Block", "Break of Structure", 
        "RSI Bullish", "RSI Bearish", 
        "EMA Bullish", "EMA Bearish",
        "MACD Bullish", "MACD Bearish",
        "VWAP Bullish", "VWAP Bearish",
        "ATR"
    ]:
        valid_confirmations.append(confirmation)

    # Calcul du SL/TP pour les signaux validés
    stop_loss, take_profit = calculate_sl_tp(entry_price, symbol)

    # Vérification des confirmations
    valid_trade, confirmations = validate_trade(valid_confirmations)

    # Si 5 confirmations minimum sont réunies, envoie l'alerte sur Telegram
    if valid_trade:
        message = (
            f"📊 **Signal TradingView**\n"
            f"💹 Actif : {symbol}\n"
            f"💰 Prix d'entrée : {entry_price:.4f}\n"
            f"🛑 Stop Loss : {stop_loss:.4f} ({'10 pips' if 'USD' in symbol and symbol != 'US30' else '20 pips'})\n"
            f"🎯 Take Profit : {take_profit:.4f}\n"
            f"📈 Risk/Reward : 1:5\n"
            f"✅ Confirmations :\n" + "\n".join(confirmations)
        )

        bot.send_message(-100123456789, message)  # Remplace avec ton ID de chat Telegram
    else:
        bot.send_message(-100123456789, "❌ Pas assez de confirmations pour valider ce trade.")

    return {"status": "success", "message": "Signal traité avec succès."}

# Lancement du bot et du serveur Flask
if __name__ == "__main__":
    WEBHOOK_URL = "https://web-production-3f98.up.railway.app/webhook"

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
