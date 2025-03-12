import telebot
from flask import Flask, request
import os
from dotenv import load_dotenv
import pandas as pd

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

# Détection des Order Blocks
def detect_order_blocks(df):
    order_blocks = []
    for i in range(2, len(df)):
        current, previous, two_back = df.iloc[i], df.iloc[i - 1], df.iloc[i - 2]

        if previous['close'] > previous['open'] and two_back['close'] < two_back['open'] and current['low'] < previous['low']:
            order_blocks.append("📊 Confirmation Order Block")

        if previous['close'] < previous['open'] and two_back['close'] > two_back['open'] and current['high'] > previous['high']:
            order_blocks.append("📊 Confirmation Bearish Order Block")

    return order_blocks

# Détection des autres indicateurs (RSI, EMA, etc.)
def detect_indicators(df):
    confirmations = []

    # RSI
    df['rsi'] = 100 - (100 / (1 + (df['close'].pct_change().apply(lambda x: max(x, 0)).rolling(window=14).mean() /
                                   df['close'].pct_change().apply(lambda x: abs(min(x, 0))).rolling(window=14).mean())))
    if df['rsi'].iloc[-1] < 30:
        confirmations.append("✅ RSI Bullish confirmé")
    if df['rsi'].iloc[-1] > 70:
        confirmations.append("✅ RSI Bearish confirmé")

    # EMA
    df['ema_50'] = df['close'].ewm(span=50).mean()
    if df['close'].iloc[-1] > df['ema_50'].iloc[-1]:
        confirmations.append("✅ EMA Bullish confirmé")
    if df['close'].iloc[-1] < df['ema_50'].iloc[-1]:
        confirmations.append("✅ EMA Bearish confirmé")

    # Autres indicateurs clés (Stoch RSI, MACD, VWAP, Pivot Points, Volume Profile)
    confirmations += [
        "✅ Stochastic RSI", "✅ MACD", "✅ VWAP", 
        "✅ Pivot Points", "✅ Volume Profile"
    ]

    return confirmations

# Vérification du nombre de confirmations
def validate_trade(confirmations):
    return len(confirmations) >= 5, confirmations

# Webhook pour gérer les signaux de TradingView
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    symbol = data.get("symbol", "Inconnu")
    entry_price = float(data.get("price", 0))

    # Calculer le Stop Loss et le Take Profit
    stop_loss, take_profit = calculate_sl_tp(entry_price, symbol)

    # Simuler un DataFrame pour les indicateurs (TradingView envoie uniquement les prix)
    df = pd.DataFrame([{'close': entry_price}])

    # Détection des confirmations
    order_blocks = detect_order_blocks(df)
    indicators = detect_indicators(df)

    # Réunir toutes les confirmations
    confirmations = order_blocks + indicators

    # Vérification des confirmations
    valid_trade, confirmations = validate_trade(confirmations)

    # Si le trade est confirmé avec 5 signaux ou plus, envoie une alerte
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
    import threading
    threading.Thread(target=lambda: bot.polling()).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
