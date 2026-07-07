from __future__ import annotations

import json
import math
import os
import random
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
PORT = int(os.environ.get("PORT", "8765"))


@dataclass
class PricePoint:
    date: str
    close: float


class MarketDataTool:
    def fetch(self, ticker: str, days: int = 90) -> tuple[list[PricePoint], str]:
        ticker = ticker.upper().strip()
        period2 = int(time.time())
        period1 = period2 - days * 24 * 60 * 60
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{ticker}?period1={period1}&period2={period2}&interval=1d"
        )
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = payload["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes = result["indicators"]["quote"][0]["close"]
            points: list[PricePoint] = []
            for ts, close in zip(timestamps, closes):
                if close is None:
                    continue
                date = time.strftime("%Y-%m-%d", time.gmtime(ts))
                points.append(PricePoint(date=date, close=float(close)))
            if len(points) >= 25:
                return points, "live"
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError, json.JSONDecodeError):
            pass
        return self._sample_data(ticker, days), "sample"

    def _sample_data(self, ticker: str, days: int) -> list[PricePoint]:
        seed = sum(ord(c) for c in ticker)
        rng = random.Random(seed)
        price = 80 + seed % 180
        drift = rng.uniform(-0.001, 0.0025)
        points: list[PricePoint] = []
        today = int(time.time())
        for i in range(days):
            shock = rng.gauss(drift, 0.018)
            price = max(5, price * (1 + shock))
            ts = today - (days - i) * 24 * 60 * 60
            points.append(PricePoint(date=time.strftime("%Y-%m-%d", time.gmtime(ts)), close=round(price, 2)))
        return points


class IndicatorTool:
    def calculate(self, points: list[PricePoint]) -> dict:
        closes = [p.close for p in points]
        if len(closes) < 25:
            return {"enoughData": False}

        returns = []
        for prev, curr in zip(closes[-21:-1], closes[-20:]):
            if prev:
                returns.append((curr - prev) / prev)

        gains = []
        losses = []
        for prev, curr in zip(closes[-15:-1], closes[-14:]):
            change = curr - prev
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))

        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

        return {
            "enoughData": True,
            "lastClose": round(closes[-1], 2),
            "sma5": round(sum(closes[-5:]) / 5, 2),
            "sma20": round(sum(closes[-20:]) / 20, 2),
            "return20dPct": round(((closes[-1] / closes[-21]) - 1) * 100, 2),
            "volatility20dPct": round(statistics.pstdev(returns) * math.sqrt(252) * 100, 2) if returns else 0,
            "rsi14": round(rsi, 2),
        }


class TrendReasoningTool:
    def judge(self, ticker: str, metrics: dict, source: str) -> dict:
        if not metrics.get("enoughData"):
            return {
                "ticker": ticker,
                "trend": "数据不足",
                "confidence": "low",
                "insight": f"{ticker} 的近期价格数据不足，暂时无法形成可靠趋势判断。",
                "metrics": metrics,
                "dataSource": source,
            }

        last_close = metrics["lastClose"]
        sma5 = metrics["sma5"]
        sma20 = metrics["sma20"]
        ret20 = metrics["return20dPct"]
        rsi = metrics["rsi14"]
        volatility = metrics["volatility20dPct"]

        if last_close > sma20 and sma5 > sma20 and ret20 > 3:
            trend = "偏强"
            confidence = "medium"
            insight = f"{ticker} 近期价格站上 20 日均线，5 日均线也高于 20 日均线，短期动能偏强。"
        elif last_close < sma20 and sma5 < sma20 and ret20 < -3:
            trend = "偏弱"
            confidence = "medium"
            insight = f"{ticker} 近期价格低于 20 日均线，短期均线也偏弱，走势承压。"
        else:
            trend = "震荡"
            confidence = "medium"
            insight = f"{ticker} 当前价格与均线关系不够一致，近 20 日更像是震荡整理。"

        if rsi >= 70:
            insight += " RSI 偏高，短线可能存在过热风险。"
        elif rsi <= 30:
            insight += " RSI 偏低，短线可能存在超卖修复可能。"

        if volatility >= 45:
            insight += " 近期波动率较高，价格变化可能更剧烈。"

        if source == "sample":
            insight += " 当前使用的是示例数据，因为实时数据源暂不可用。"

        return {
            "ticker": ticker,
            "trend": trend,
            "confidence": confidence,
            "insight": insight,
            "metrics": metrics,
            "dataSource": source,
        }


class StockTrendAgent:
    def __init__(self) -> None:
        self.market = MarketDataTool()
        self.indicators = IndicatorTool()
        self.reasoner = TrendReasoningTool()

    def analyze(self, tickers: list[str], days: int = 90) -> dict:
        results = []
        for ticker in tickers:
            cleaned = "".join(ch for ch in ticker.upper().strip() if ch.isalnum() or ch in ".-")
            if not cleaned:
                continue
            points, source = self.market.fetch(cleaned, days=days)
            metrics = self.indicators.calculate(points)
            result = self.reasoner.judge(cleaned, metrics, source)
            result["prices"] = [{"date": p.date, "close": p.close} for p in points[-60:]]
            results.append(result)
        return {"results": results, "disclaimer": "仅用于趋势观察和 Agent demo，不构成投资建议。"}


AGENT = StockTrendAgent()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/analyze":
            query = parse_qs(parsed.query)
            tickers = query.get("tickers", ["AAPL,MSFT,NVDA"])[0].split(",")
            days = int(query.get("days", ["90"])[0])
            self._json(AGENT.analyze(tickers, days=days))
            return
        if parsed.path == "/":
            self.path = "/static/index.html"
        return super().do_GET()

    def translate_path(self, path: str) -> str:
        if path.startswith("/static/"):
            return str(ROOT / path.lstrip("/"))
        return str(STATIC / "index.html")

    def _json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Stock Trend Insight Agent running at http://localhost:{PORT}")
    server.serve_forever()
