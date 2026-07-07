# 部署到公网

如果想让所有人通过网址访问这个 Agent，需要把项目部署到公网平台。

## 最简单路线：Render

1. 注册 Render：
   https://render.com

2. 把 `stock-trend-agent` 项目上传到 GitHub。

3. 在 Render 创建 New Web Service。

4. 选择这个 GitHub 仓库。

5. 设置：

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

6. 部署完成后，Render 会给你一个公网网址，例如：

```text
https://stock-trend-agent.onrender.com
```

别人就可以通过这个网址访问。

## 注意

- `localhost` 只能自己电脑访问。
- 公网部署后，别人访问的是云服务器上的版本。
- 如果你后面接入真实 API key，不要写在代码里，要放到环境变量。
