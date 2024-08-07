from flask import Flask, request, render_template
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare():
    ticker1 = request.form['company1']
    ticker2 = request.form['company2']
    days = int(request.form['days'])
    results = fetch_and_display_data(ticker1, ticker2, days)
    return render_template('results.html', results=results, ticker1=ticker1, ticker2=ticker2)

def fetch_and_display_data(ticker1, ticker2, days):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    stock1_data = yf.download(ticker1, start=start_date, end=end_date)
    stock2_data = yf.download(ticker2, start=start_date, end=end_date)
    market_data = yf.download('^NSEI', start=start_date, end=end_date)

    if stock1_data.empty or stock2_data.empty or market_data.empty:
        return {'error': 'One or both stock tickers are invalid or no data is available for the given period.'}

    stock1_data['Daily_Return'] = stock1_data['Adj Close'].pct_change()
    stock2_data['Daily_Return'] = stock2_data['Adj Close'].pct_change()
    market_data['Daily_Return'] = market_data['Adj Close'].pct_change()

    if 'Daily_Return' not in stock1_data.columns or 'Daily_Return' not in stock2_data.columns or 'Daily_Return' not in market_data.columns:
        return {'error': 'Failed to calculate daily returns for one or more stocks.'}

    daily_returns_div = create_daily_returns_plot(stock1_data, stock2_data, ticker1, ticker2, days)
    cumulative_returns_div = create_cumulative_returns_plot(stock1_data, stock2_data, ticker1, ticker2, days)
    volatility_div = create_volatility_plot(stock1_data, stock2_data, ticker1, ticker2, days)
    beta_stock1, beta_stock2, conclusion = calculate_beta(stock1_data, stock2_data, market_data, ticker1, ticker2)

    mse_stock1 = ((stock1_data['Daily_Return'].dropna() - market_data['Daily_Return'].dropna()) ** 2).mean()
    mse_stock2 = ((stock2_data['Daily_Return'].dropna() - market_data['Daily_Return'].dropna()) ** 2).mean()

    return {
        'daily_returns_div': daily_returns_div,
        'cumulative_returns_div': cumulative_returns_div,
        'volatility_div': volatility_div,
        'beta_stock1': beta_stock1,
        'beta_stock2': beta_stock2,
        'conclusion': conclusion,
        'mse_stock1': mse_stock1,
        'mse_stock2': mse_stock2
    }

def create_daily_returns_plot(stock1_data, stock2_data, ticker1, ticker2, days):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock1_data.index, y=stock1_data['Daily_Return'], mode='lines', name=ticker1, line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=stock2_data.index, y=stock2_data['Daily_Return'], mode='lines', name=ticker2, line=dict(color='green')))
    fig.update_layout(title=f'Daily Returns for {ticker1} and {ticker2} (Last {days} Days)', xaxis_title='Date', yaxis_title='Daily Return', legend=dict(x=0.02, y=0.95))
    return pio.to_html(fig, full_html=False)

def create_cumulative_returns_plot(stock1_data, stock2_data, ticker1, ticker2, days):
    stock1_cumulative_return = (1 + stock1_data['Daily_Return']).cumprod() - 1
    stock2_cumulative_return = (1 + stock2_data['Daily_Return']).cumprod() - 1

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock1_cumulative_return.index, y=stock1_cumulative_return, mode='lines', name=ticker1, line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=stock2_cumulative_return.index, y=stock2_cumulative_return, mode='lines', name=ticker2, line=dict(color='green')))
    fig.update_layout(title=f'Cumulative Returns for {ticker1} and {ticker2} (Last {days} Days)', xaxis_title='Date', yaxis_title='Cumulative Return', legend=dict(x=0.02, y=0.95))
    return pio.to_html(fig, full_html=False)

def create_volatility_plot(stock1_data, stock2_data, ticker1, ticker2, days):
    stock1_volatility = stock1_data['Daily_Return'].std()
    stock2_volatility = stock2_data['Daily_Return'].std()

    fig = go.Figure()
    fig.add_bar(x=[ticker1, ticker2], y=[stock1_volatility, stock2_volatility], text=[f'{stock1_volatility:.4f}', f'{stock2_volatility:.4f}'], textposition='auto', marker=dict(color=['blue', 'green']))
    fig.update_layout(title=f'Volatility Comparison (Last {days} Days)', xaxis_title='Stock', yaxis_title='Volatility (Standard Deviation)', bargap=0.5)
    return pio.to_html(fig, full_html=False)

def calculate_beta(stock1_data, stock2_data, market_data, ticker1, ticker2):
    cov_stock1 = stock1_data['Daily_Return'].cov(market_data['Daily_Return'])
    var_market = market_data['Daily_Return'].var()
    beta_stock1 = cov_stock1 / var_market

    cov_stock2 = stock2_data['Daily_Return'].cov(market_data['Daily_Return'])
    beta_stock2 = cov_stock2 / var_market

    conclusion = f"{ticker1} is more volatile (higher Beta) compared to {ticker2}." if beta_stock1 > beta_stock2 else f"{ticker2} is more volatile (higher Beta) compared to {ticker1}."

    return beta_stock1, beta_stock2, conclusion

if __name__ == '__main__':
    app.run(debug=False)
