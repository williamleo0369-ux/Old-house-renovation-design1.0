<template>
  <div class="backtest-view">
    <div class="backtest-config">
        <h3>策略配置</h3>
        <div class="form-group">
            <label for="backtest-symbol">股票代码</label>
            <input type="text" id="backtest-symbol" v-model="backtestSymbol" placeholder="e.g., 000300.SH">
        </div>
        <div class="form-group">
            <label for="start-date">开始日期</label>
            <input type="date" id="start-date" v-model="startDate">
        </div>
        <div class="form-group">
            <label for="end-date">结束日期</label>
            <input type="date" id="end-date" v-model="endDate">
        </div>
        <div class="form-group">
            <label for="initial-capital">初始资金</label>
            <input type="number" id="initial-capital" v-model="initialCapital">
        </div>
        <div class="form-group">
            <label for="strategy">策略 (自然语言)</label>
            <textarea id="strategy" v-model="strategy" rows="4" placeholder="例如: 每月第一个交易日定投1000元"></textarea>
        </div>
        <button @click="runBacktest" class="run-backtest-btn" :disabled="isFetchingBacktest">
            {{ isFetchingBacktest ? '回测运行中...' : '开始回测' }}
        </button>
    </div>
    <div class="backtest-results">
        <div class="metric-cards">
            <div class="metric-card">
                <h4>年化收益率</h4>
                <div class="value" :class="getMetricClass(backtestResult.annualized_return)">{{ formatMetric(backtestResult.annualized_return, '%') }}</div>
            </div>
            <div class="metric-card">
                <h4>最大回撤</h4>
                <div class="value down">{{ formatMetric(backtestResult.max_drawdown, '%') }}</div>
            </div>
            <div class="metric-card">
                <h4>夏普比率</h4>
                <div class="value">{{ formatMetric(backtestResult.sharpe_ratio) }}</div>
            </div>
            <div class="metric-card">
                <h4>胜率</h4>
                <div class="value">{{ formatMetric(backtestResult.win_rate, '%') }}</div>
            </div>
        </div>
        <div id="backtest-chart-container">
            <div v-if="isFetchingBacktest" style="text-align: center; padding-top: 50px;">正在生成回测净值曲线...</div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import Plotly from 'plotly.js/dist/plotly';

const API_BASE_URL = 'http://127.0.0.1:8000';

const backtestSymbol = ref('000300.SH');
const startDate = ref('2022-01-01');
const endDate = ref('2023-01-01');
const initialCapital = ref(100000);
const strategy = ref('每月第一个交易日定投1000元');
const backtestResult = ref({});
const isFetchingBacktest = ref(false);
const backtestChart = ref(null);

const runBacktest = async () => {
    isFetchingBacktest.value = true;
    backtestResult.value = {};
    try {
        const response = await fetch(`${API_BASE_URL}/api/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: backtestSymbol.value,
                start_date: startDate.value,
                end_date: endDate.value,
                initial_capital: initialCapital.value,
                strategy: strategy.value
            })
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Backtest failed');
        }
        backtestResult.value = await response.json();
        nextTick(() => {
            renderBacktestChart(backtestResult.value.equity_curve);
        });
    } catch (error) {
        console.error('Error running backtest:', error);
        alert(`回测失败: ${error.message}`);
    } finally {
        isFetchingBacktest.value = false;
    }
};

const renderBacktestChart = (equityCurve) => {
    const container = document.getElementById('backtest-chart-container');
    if (!container) return;
    container.innerHTML = ''; // Clear previous chart
    if (!equityCurve || equityCurve.length === 0) return;

    const plotData = [{
        x: equityCurve.map(d => d.date),
        y: equityCurve.map(d => d.equity),
        type: 'scatter',
        mode: 'lines',
        name: '策略净值',
        line: { color: 'var(--accent-color)' }
    }];

    const layout = {
        title: '策略净值曲线',
        xaxis: { title: '日期' },
        yaxis: { title: '净值' },
        margin: { l: 50, r: 20, b: 40, t: 40 },
        paper_bgcolor: 'var(--content-bg)',
        plot_bgcolor: 'var(--content-bg)',
        font: { color: 'var(--text-color)' }
    };

    Plotly.newPlot(container, plotData, layout, { responsive: true });
};

const formatMetric = (value, unit = '') => {
    if (typeof value !== 'number') return 'N/A';
    if (unit === '%') return `${(value * 100).toFixed(2)}%`;
    return value.toFixed(2);
};

const getMetricClass = (value) => {
    if (typeof value !== 'number') return '';
    return value >= 0 ? 'up' : 'down';
};

</script>

<style scoped>
/* Backtesting Styles */
.backtest-view { display: grid; grid-template-columns: 320px 1fr; gap: 24px; height: 100%; }
.backtest-config { background-color: var(--content-bg); border-radius: 8px; padding: 20px; border: 1px solid var(--border-color); }
.backtest-results { display: flex; flex-direction: column; gap: 24px; }
.backtest-config h3 { margin-top: 0; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.form-group input, .form-group textarea { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 14px; box-sizing: border-box; }
.run-backtest-btn { width: 100%; padding: 10px; background-color: var(--accent-color); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
.metric-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }
.metric-card { background-color: var(--content-bg); border-radius: 8px; padding: 20px; border: 1px solid var(--border-color); text-align: center; }
.metric-card h4 { margin: 0 0 8px 0; font-size: 14px; color: var(--text-color-secondary); }
.metric-card .value { font-size: 24px; font-weight: 600; color: var(--accent-color); }
.metric-card .value.up { color: var(--price-up-color); }
.metric-card .value.down { color: var(--price-down-color); }
#backtest-chart-container { flex-grow: 1; background-color: var(--content-bg); border-radius: 8px; border: 1px solid var(--border-color); }
</style>