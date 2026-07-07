# Stock Trend Insight Agent

一个最小可运行的股票趋势洞察 Agent demo。

## 它最终是什么

这是一个本地网页工具。用户打开网页后输入股票代码，例如 `AAPL, MSFT, NVDA`，Agent 会：

1. 获取近期价格数据
2. 计算短期/中期均线、近 20 日涨跌幅、波动率、RSI
3. 判断趋势状态
4. 输出一句简洁的人类可读洞察

它不是投资建议，只是演示“Agent 如何把数据读取、规则分析、前端展示串起来”。

## 如何运行

在这个文件夹中运行：

```bash
python3 app.py
```

如果系统自带 `python3` 不可用，可以使用 Codex 内置 Python：

```bash
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 app.py
```

然后打开：

```text
http://localhost:8765
```

## 制作流程

这个 demo 按照一个真实 Agent 的基本结构拆成 4 层：

```text
用户界面
  ↓
Agent 控制器
  ↓
工具模块
  - 行情数据读取
  - 指标计算
  - 趋势判断
  ↓
结构化输出
```

## 文件说明

```text
app.py
  本地后端服务和 Agent 逻辑

static/index.html
  前端页面

static/styles.css
  页面样式

static/app.js
  前端交互逻辑

agent_prompt.md
  这个 Agent 的角色、目标、工具、规则、输出定义
```

## 下一步可以升级

- 接入更稳定的行情数据源
- 增加 K 线图
- 增加新闻摘要
- 增加财报日期、成交量异常、板块对比
- 增加用户自选股票列表
- 增加定时监控和提醒
