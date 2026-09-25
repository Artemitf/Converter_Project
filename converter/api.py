import aiohttp
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta
from database import get_all_notifications, update_notification_time

BYBIT_API_URL = 'https://api.bybit.com/v5/market/tickers'

async def get_ticker_data(symbol: str) -> Optional[Dict]:

    try:
        async with aiohttp.ClientSession() as session:
            params = {'category': 'spot', 'symbol': symbol.upper()}
            async with session.get(BYBIT_API_URL, params=params) as response:
                data = await response.json()
                if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                    ticker = data['result']['list'][0]
                    return {
                        'last_price': float(ticker['lastPrice']),
                        'prev_price_24h': float(ticker.get('prevPrice24h', 0)),
                        'price_24h_pcnt': float(ticker.get('price24hPcnt', 0)) * 100
                    }
                    
    except Exception as e:
        print(f"Error fetching ticker data for {symbol}: {e}")
    return None

async def get_price_from_bybit(symbol: str) -> Optional[float]:

    data = await get_ticker_data(symbol)
    if data:
        return data['last_price']
    return None

async def convert_currency(currency1: str, amount: float, currency2: str) -> Optional[float]:

    try:
        if len(currency1) <= 4 and len(currency2) <= 4:

            price = await get_price_from_bybit(f"{currency1.upper()}{currency2.upper()}")
            if price:
                return amount * price
            
            # обратная пара
            price = await get_price_from_bybit(f"{currency2.upper()}{currency1.upper()}")
            if price:
                return amount / price
            
            #через USDT
            price1 = await get_price_from_bybit(f"{currency1.upper()}USDT")
            price2 = await get_price_from_bybit(f"{currency2.upper()}USDT")
            if price1 and price2:
                return (amount * price1) / price2
            
    except Exception as e:
        print(f"Conversion error: {e}")
    
    return None

async def check_notifications(bot):
    while True:
        try:
            notifications = await get_all_notifications()
            for user_id, asset, percent_change, last_triggered in notifications:
                if last_triggered:
                    last_time = datetime.fromisoformat(last_triggered)
                    if datetime.now() - last_time < timedelta(minutes=15):
                        continue
                
                ticker_data = await get_ticker_data(f"{asset}USDT")
                if ticker_data:
                    # процент изменения за 24 часа
                    change_percent = ticker_data['price_24h_pcnt']
                    
                    if change_percent > 0:
                        message = f"🟢 {asset} вырос на {abs(change_percent):.2f}%!"
                    else:
                        message = f"🔴 {asset} упал на {abs(change_percent):.2f}%!"
                        
                    await bot.send_message(user_id, message)
                    await update_notification_time(user_id, asset)
        
        except Exception as e:
            print(f"Notification check error: {e}")
        
        await asyncio.sleep(60)