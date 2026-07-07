const runButton = document.querySelector("#run");
const tickersInput = document.querySelector("#tickers");
const daysSelect = document.querySelector("#days");
const statusEl = document.querySelector("#status");
const resultsEl = document.querySelector("#results");

function badgeClass(trend) {
  if (trend === "偏弱") return "badge weak";
  if (trend === "震荡" || trend === "数据不足") return "badge flat";
  return "badge";
}

function metric(label, value, suffix = "") {
  const display = value === undefined || value === null ? "N/A" : `${value}${suffix}`;
  return `<div class="metric"><span>${label}</span><b>${display}</b></div>`;
}

function renderResult(item) {
  const m = item.metrics || {};
  return `
    <article class="card">
      <div class="card-head">
        <div class="ticker">${item.ticker}</div>
        <div class="${badgeClass(item.trend)}">${item.trend}</div>
      </div>
      <div class="insight">${item.insight}</div>
      <div class="metrics">
        ${metric("最新收盘", m.lastClose)}
        ${metric("5 日均线", m.sma5)}
        ${metric("20 日均线", m.sma20)}
        ${metric("20 日涨跌", m.return20dPct, "%")}
        ${metric("20 日年化波动", m.volatility20dPct, "%")}
        ${metric("RSI 14", m.rsi14)}
      </div>
      <div class="source">数据源：${item.dataSource === "live" ? "实时行情接口" : "示例数据"}</div>
    </article>
  `;
}

async function analyze() {
  const tickers = tickersInput.value.trim();
  const days = daysSelect.value;
  if (!tickers) {
    statusEl.textContent = "请输入至少一个股票代码。";
    return;
  }

  runButton.disabled = true;
  statusEl.textContent = "Agent 正在读取数据并分析趋势...";
  resultsEl.innerHTML = "";

  try {
    const response = await fetch(`/api/analyze?tickers=${encodeURIComponent(tickers)}&days=${days}`);
    const payload = await response.json();
    resultsEl.innerHTML = payload.results.map(renderResult).join("");
    statusEl.textContent = payload.disclaimer;
  } catch (error) {
    statusEl.textContent = "分析失败，请确认本地服务正在运行。";
  } finally {
    runButton.disabled = false;
  }
}

runButton.addEventListener("click", analyze);
analyze();
