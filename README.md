# QuantVisual Monitor (量化可视化监控平台)

这是一个基于 Python (FastAPI) 和 Vue 3 的股票量化分析与网格交易监控平台。支持 A 股、港股、美股的实时行情查询、K 线图展示、网格交易策略模拟以及微信消息推送。

## ✨ 功能特性 (Features)

- **多市场支持**: 支持 A 股 (自动识别沪深)、港股、美股的实时行情查询。
- **专业 K 线图**: 集成 TradingView Lightweight Charts，提供流畅的交互式 K 线体验。
- **网格交易策略**: 
  - 可视化配置网格上/下限。
  - 实时监控价格触网状态。
  - 动态计算持仓盈亏 (模拟)。
  - 炫酷的网格进度条可视化。
- **实时监控面板**:
  - 自选股 (Watchlist) 管理与实时刷新。
  - 账户资产概览。
- **微信通知**: 集成 WxPusher，当价格触及网格线时自动推送到微信。
- **视觉特效**: 包含粒子背景与交互动画，提供现代化的 UI 体验。

## 🛠️ 技术栈 (Tech Stack)

- **后端**: Python 3, FastAPI, APScheduler, yfinance
- **前端**: Vue 3 (Composition API), Tailwind CSS, Lightweight Charts, tsParticles
- **部署**: Uvicorn

## 🚀 快速开始 (Getting Started)

### 1. 安装依赖

确保你已经安装了 Python 3.8+。

```bash
cd backend
pip install -r requirements.txt
```

### 2. 运行服务

在 `backend` 目录下运行：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问应用

打开浏览器访问: http://localhost:8000

## 📝 使用指南

1. **查询股票**: 在顶部搜索框输入代码（如 `600519`, `0700`, `AAPL`），选择对应的市场（CN/HK/US）。
2. **添加自选**: 点击股票名称旁的 ★ 图标加入关注列表。
3. **启动策略**: 
   - 在“参数配置”面板输入网格上限和下限。
   - 输入你的 WxPusher UID（可选，用于接收通知）。
   - 点击“启动监控策略”。
4. **查看状态**: 页面中间的进度条会实时显示当前价格在网格中的位置。

## ⚠️ 注意事项

- 本项目使用 `yfinance` 获取数据，可能会有访问频率限制。
- 交易逻辑目前为**模拟盘**，仅供学习和回测分析使用，不涉及真实资金交易。

## License

MIT
