from flask import Flask, request, jsonify
from transformers import pipeline
import yfinance as yf
from bs4 import BeautifulSoup
import requests
import pandas as pd

app = Flask(__name__)
sentiment_model = pipeline("sentiment-analysis")

def get_latest_news(stock):
    try:
        url = f"https://www.google.com/search?q={stock}+stock+news"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        headlines = soup.find_all("div", class_="BNeawe vvjwJb AP7Wnd")
        return [h.get_text() for h in headlines[:5]]
    except Exception:
        return []

@app.route('/predict')
def predict():
    symbol = request.args.get('symbol')
    period = request.args.get('period', '5d')

    try:
        stock = yf.Ticker(symbol + ".NS")
        hist = stock.history(period=period)
        if hist.empty:
            return jsonify({"error": f"No data for {symbol}"}), 400

        balance = stock.quarterly_balance_sheet
        cashflow = stock.quarterly_cashflow

        def safe_get(df, key):
            return df.loc[key].iloc[0] if key in df.index else 0

        net_assets = safe_get(balance, 'Net Tangible Assets')
        short_debt = safe_get(balance, 'Short Long Term Debt') + safe_get(balance, 'Long Term Debt')

        operating_cash = safe_get(cashflow, 'Total Cash From Operating Activities') or safe_get(cashflow, 'Operating Cash Flow')
        capex = safe_get(cashflow, 'Capital Expenditures') or safe_get(cashflow, 'Capital Expenditure')

        debt_ratio = short_debt / net_assets if net_assets else 0
        free_cash_flow = operating_cash - capex

        closing = hist['Close'].tolist()
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        trend = "Up" if closing[-1] > closing[0] else "Down"

        news = get_latest_news(symbol)
        if not news:
            news = ["No recent news"]
            sentiment_trend = "Neutral"
            confidence = "0.00%"
        else:
            sentiments = sentiment_model(news)
            pos = sum(1 for s in sentiments if s['label'] == 'POSITIVE')
            sentiment_trend = "Up" if pos > len(news) / 2 else "Down"
            confidence = f"{(pos / len(news)) * 100:.2f}%"

        final = "Up"
        reason = []
        if trend == "Down":
            final = "Down"
            reason.append("Price trending down")
        if sentiment_trend == "Down":
            final = "Down"
            reason.append("Negative sentiment")
        if debt_ratio > 0.6:
            final = "Down"
            reason.append("High debt ratio")
        if free_cash_flow < 0:
            final = "Down"
            reason.append("Negative free cash flow")
        if final == "Up":
            reason.append("Strong fundamentals + sentiment")

        return jsonify({
            "symbol": symbol,
            "trend_based_on_price": trend,
            "trend_based_on_news": sentiment_trend,
            "fundamentals": {
                "debt_ratio": f"{debt_ratio:.2f}",
                "free_cash_flow": f"{free_cash_flow:.2f}"
            },
            "prediction": final,
            "confidence": confidence,
            "reasoning": reason,
            "closing_prices": closing,
            "dates": dates,
            "news_headlines": news
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
