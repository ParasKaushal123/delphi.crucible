from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from state.user_profile import UserProfile, Position
import json
import datetime
import requests
import httpx
import asyncio

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])
MOCK_USER_ID = "demo_user"

class AddPositionReq(BaseModel):
    ticker: str
    shares: int
    threshold: str = ""

@router.get("")
async def get_portfolio(request: Request):
    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    profile = UserProfile.model_validate_json(data) if data else UserProfile(user_id=MOCK_USER_ID)
    
    portfolio_data = []
    total_value = 0
    total_cost = 0
    
    if profile.portfolio:
        tickers = list(profile.portfolio.keys())
        try:
            current_prices = {}
            async with httpx.AsyncClient() as client:
                async def fetch_price(t):
                    if t.upper() == "MOCK":
                        import time
                        cycle = 420
                        elapsed = time.time() % cycle
                        if elapsed < 210:
                            current_price = 70.0 + (50.0 * (elapsed / 210.0))
                        else:
                            current_price = 120.0 - (50.0 * ((elapsed - 210) / 210.0))
                        return t, round(current_price, 2)
                    try:
                        res = await client.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{t}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10.0)
                        if res.status_code == 200:
                            data = res.json()
                            return t, data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                    except:
                        pass
                    return t, None

                tasks = [fetch_price(t) for t in tickers]
                results = await asyncio.gather(*tasks)
                
                for t, price in results:
                    if price is not None:
                        current_prices[t] = price
        except Exception as e:
            print(f"requests error: {e}")
            current_prices = {}

        for t, pos in profile.portfolio.items():
            current_price = current_prices.get(t, pos.buy_price)
            current_val = current_price * pos.shares
            cost = pos.buy_price * pos.shares
            total_value += current_val
            total_cost += cost
            portfolio_data.append({
                "ticker": t,
                "buy_price": pos.buy_price,
                "shares": pos.shares,
                "threshold": pos.threshold,
                "current_price": current_price,
                "total_value": current_val,
                "return_pct": ((current_price - pos.buy_price) / pos.buy_price) * 100 if pos.buy_price else 0
            })
            
    return {
        "portfolio": portfolio_data,
        "summary": {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_profit": total_value - total_cost,
            "total_return_pct": ((total_value - total_cost) / total_cost * 100) if total_cost else 0
        }
    }

@router.post("/add")
async def add_position(req: AddPositionReq, request: Request):
    import requests
    try:
        # Bypass yfinance completely for live quote to avoid their internal rate limit blocks
        res = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{req.ticker.upper()}", headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code != 200:
            raise ValueError("Rate limited or invalid ticker")
        data = res.json()
        current_price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ticker symbol: {req.ticker.upper()}")

    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    profile = UserProfile.model_validate_json(data) if data else UserProfile(user_id=MOCK_USER_ID)
    
    # If already own, average the price or just overwrite? Overwriting for simplicity in paper trading demo
    profile.portfolio[req.ticker.upper()] = Position(buy_price=current_price, shares=req.shares, threshold=req.threshold)
    await store._redis.set(f"user_profile:{MOCK_USER_ID}", profile.model_dump_json())
    
    await store._redis.lpush(
        f"user_history:{MOCK_USER_ID}", 
        json.dumps({
            "type": "transaction", 
            "action": "ADD", 
            "ticker": req.ticker.upper(), 
            "shares": req.shares, 
            "price": current_price,
            "timestamp": datetime.datetime.now().isoformat()
        })
    )
    
    return {"status": "success", "portfolio": profile.portfolio}

@router.post("/remove")
async def remove_position(req: dict, request: Request):
    import requests
    ticker = req.get("ticker", "").upper()
    
    try:
        res = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}", headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code != 200:
            current_price = 0
        else:
            data = res.json()
            current_price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except:
        current_price = 0

    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    profile = UserProfile.model_validate_json(data) if data else UserProfile(user_id=MOCK_USER_ID)
    
    if ticker in profile.portfolio:
        profile.portfolio[ticker].shares = 0
        await store._redis.set(f"user_profile:{MOCK_USER_ID}", profile.model_dump_json())
        await store._redis.lpush(
            f"user_history:{MOCK_USER_ID}", 
            json.dumps({
                "type": "transaction", 
                "action": "SELL", 
                "ticker": ticker,
                "price": current_price,
                "timestamp": datetime.datetime.now().isoformat()
            })
        )
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Position not found")

@router.get("/history")
async def get_history(request: Request):
    store = request.app.state.session_store
    data = await store._redis.lrange(f"user_history:{MOCK_USER_ID}", 0, -1)
    
    history = []
    for item in data:
        try:
            h = json.loads(item)
            if h.get("type") == "transaction":
                history.append(h)
        except:
            pass
    return {"history": history}

@router.get("/chart")
async def get_portfolio_chart(request: Request):
    range_param = request.query_params.get("range", "1mo")
    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    profile = UserProfile.model_validate_json(data) if data else UserProfile(user_id=MOCK_USER_ID)
    
    if not profile.portfolio:
        return {"chart": []}
        
    tickers = list(profile.portfolio.keys())
    
    if range_param == "1d":
        interval = "5m"
        dt_format = "%I:%M %p"
    elif range_param == "1y":
        interval = "1wk"
        dt_format = "%b %Y"
    else: # 1mo
        interval = "1d"
        dt_format = "%b %d"
        
    try:
        chart_data = []
        async with httpx.AsyncClient() as client:
            async def fetch_chart(t):
                if t.upper() == "MOCK":
                    import time
                    now = int(time.time())
                    
                    cycle = 420
                    timestamps = [now - (30-i)*86400 for i in range(30)]
                    closes = []
                    for ts in timestamps:
                        elapsed = ts % cycle
                        if elapsed < 210:
                            closes.append(70.0 + (50.0 * (elapsed / 210.0)))
                        else:
                            closes.append(120.0 - (50.0 * ((elapsed - 210) / 210.0)))
                    
                    return t, {
                        "chart": {
                            "result": [{
                                "timestamp": timestamps,
                                "indicators": {"quote": [{"close": closes}]}
                            }]
                        }
                    }
                    
                try:
                    res = await client.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{t}?range={range_param}&interval={interval}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10.0)
                    if res.status_code == 200:
                        return t, res.json()
                except:
                    pass
                return t, None

            tasks = [fetch_chart(t) for t in tickers]
            results = await asyncio.gather(*tasks)

            stock_series = {t: {} for t in tickers}
            date_to_ts = {}

            for t, data in results:
                if not data:
                    continue
                timestamps = data["chart"]["result"][0].get("timestamp")
                if not timestamps:
                    continue
                closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                
                # Store series per stock
                for i in range(len(timestamps)):
                    if closes[i] is None:
                        continue
                    dt = datetime.datetime.fromtimestamp(timestamps[i]).strftime(dt_format)
                    if dt not in date_to_ts:
                        date_to_ts[dt] = timestamps[i]
                    stock_series[t][dt] = closes[i] * profile.portfolio[t].shares
                    
            # Sort all unique dates chronologically
            sorted_dates = sorted(date_to_ts.keys(), key=lambda d: date_to_ts[d])
            
            # Build chart_data with forward-filling for missing days (like weekends)
            chart_data = []
            last_known = {t: 0 for t in tickers}
            
            for dt in sorted_dates:
                total_val = 0
                for t in tickers:
                    if dt in stock_series[t]:
                        last_known[t] = stock_series[t][dt]
                    total_val += last_known[t]
                chart_data.append({"date": dt, "value": total_val, "raw_ts": date_to_ts[dt]})
        
        # Sort by timestamp
        chart_data.sort(key=lambda x: x.get("raw_ts", 0))
        
        # Round values
        for item in chart_data:
            item["value"] = round(item["value"], 2)
            
        return {"chart": chart_data}
    except Exception as e:
        print(f"Chart requests error: {e}")
        return {"chart": []}

@router.get("/stock-chart/{ticker}")
async def get_individual_stock_chart(ticker: str, request: Request):
    range_param = request.query_params.get("range", "1mo")
    if range_param == "1d":
        interval = "5m"
        dt_format = "%I:%M %p"
    elif range_param == "1y":
        interval = "1wk"
        dt_format = "%b %Y"
    else: # 1mo
        interval = "1d"
        dt_format = "%b %d"
        
    try:
        if ticker.upper() == "MOCK":
            import time
            now = int(time.time())
            
            cycle = 420
            timestamps = [now - (30-i)*86400 for i in range(30)]
            closes = []
            for ts in timestamps:
                elapsed = ts % cycle
                if elapsed < 210:
                    closes.append(70.0 + (50.0 * (elapsed / 210.0)))
                else:
                    closes.append(120.0 - (50.0 * ((elapsed - 210) / 210.0)))
            
            chart_data = []
            for i in range(len(timestamps)):
                dt = datetime.datetime.fromtimestamp(timestamps[i]).strftime(dt_format)
                chart_data.append({"date": dt, "value": round(closes[i], 2), "raw_ts": timestamps[i]})
            return {"chart": chart_data}
            
        import httpx
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker.upper()}?range={range_param}&interval={interval}", headers={'User-Agent': 'Mozilla/5.0'}, timeout=10.0)
            
        if res.status_code != 200:
            return {"chart": []}
        data = res.json()
        timestamps = data["chart"]["result"][0]["timestamp"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        
        chart_data = []
        for i in range(len(timestamps)):
            if closes[i] is None:
                continue
            dt = datetime.datetime.fromtimestamp(timestamps[i]).strftime(dt_format)
            chart_data.append({"date": dt, "value": round(closes[i], 2), "raw_ts": timestamps[i]})
        return {"chart": chart_data}
    except Exception as e:
        print(f"Individual chart error: {e}")
        return {"chart": []}
