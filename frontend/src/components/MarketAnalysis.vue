<template>
  <div class="analysis-grid">
    <div class="analysis-header">
        <div class="stock-info">
            <div class="stock-name">
                <h2 v-if="stockDetails.name">{{ stockDetails.name }}</h2>
                <span v-if="stockDetails.symbol">{{ stockDetails.symbol }}</span>
            </div>
            <div v-if="stockDetails.current_price" class="stock-price" :class="priceChangePercent >= 0 ? 'price-up' : 'price-down'">
                {{ stockDetails.current_price?.toFixed(2) }}
            </div>
            <div v-if="stockDetails.price_change" class="stock-change" :class="priceChangePercent >= 0 ? 'price-up' : 'price-down'">
                <span>{{ stockDetails.price_change?.toFixed(2) }}</span>
                <span>{{ priceChangePercent?.toFixed(2) }}%</span>
            </div>
        </div>
        <div class="search-bar">
            <input type="text" v-model="searchSymbol" @keyup.enter="changeSymbol" placeholder="输入股票/ETF代码">
            <button @click="changeSymbol">查询</button>
        </div>
    </div>
    <div class="interval-tabs">
        <button @click="changeInterval('hourly')" :class="{ active: selectedInterval === 'hourly' }">时</button>
        <button @click="changeInterval('daily')" :class="{ active: selectedInterval === 'daily' }">日</button>
        <button @click="changeInterval('weekly')" :class="{ active: selectedInterval === 'weekly' }">周</button>
        <button @click="changeInterval('monthly')" :class="{ active: selectedInterval === 'monthly' }">月</button>
    </div>
    <div id="chart-container"></div>
    <div id="intelligence-container" v-if="intelligentAnalysis">
        <div class="intelligence-header" @click="intelligenceExpanded = !intelligenceExpanded">
            <h3>实时情报对冲</h3>
            <span>{{ intelligenceExpanded ? '收起' : '展开' }}</span>
        </div>
        <div v-show="intelligenceExpanded" class="intelligence-content-wrapper">
            <div class="pulse-dashboard">
                <div class="pulse-labels">
                    <span>机构看点</span>
                    <span>散户槽点</span>
                </div>
                <div class="pulse-bar-container">
                    <div class="pulse-bar" :style="{ width: pulseWidth }"></div>
                </div>
                <div class="pulse-score">
                    情绪评分: {{ intelligentAnalysis.score?.toFixed(2) }}
                </div>
            </div>
            <div class="intelligence-content">
                <div class="intelligence-column logic-column">
                    <h4>机构看点 (Logic)</h4>
                    <p v-if="isFetchingIntelligentAnalysis">加载中...</p>
                    <p v-else-if="intelligentAnalysis.logic">{{ intelligentAnalysis.logic }}</p>
                    <p v-else>暂无数据</p>
                </div>
                <div class="intelligence-column emotion-column" :style="{ backgroundColor: intelligentAnalysis.score < -0.5 ? 'rgba(246, 53, 63, 0.1)' : '' }">
                    <h4>散户槽点 (Emotion)</h4>
                    <p v-if="isFetchingIntelligentAnalysis">加载中...</p>
                    <p v-else-if="intelligentAnalysis.emotion">{{ intelligentAnalysis.emotion }}</p>
                    <p v-else>暂无数据</p>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { createChart } from 'lightweight-charts';

const API_BASE_URL = 'http://127.0.0.1:8000';

const searchSymbol = ref('000300.SH');
const stockDetails = ref({});
const selectedInterval = ref('daily');
const chart = ref(null);
const candleSeries = ref(null);
const intelligentAnalysis = ref({});
const isFetchingIntelligentAnalysis = ref(false);
const intelligenceExpanded = ref(true);

const priceChangePercent = computed(() => {
    if (stockDetails.value.current_price && stockDetails.value.previous_close) {
        return ((stockDetails.value.current_price - stockDetails.value.previous_close) / stockDetails.value.previous_close) * 100;
    }
    return 0;
});

const pulseWidth = computed(() => {
    if (!intelligentAnalysis.value || typeof intelligentAnalysis.value.score !== 'number') return '50%';
    const score = Math.max(-1, Math.min(1, intelligentAnalysis.value.score));
    const width = (score + 1) * 50;
    return `${width}%`;
});

const fetchStockData = async () => {
    if (!searchSymbol.value) return;
    try {
        const response = await fetch(`${API_BASE_URL}/api/market_data/${searchSymbol.value}?interval=${selectedInterval.value}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        stockDetails.value = data.details;
        
        if (candleSeries.value) {
            candleSeries.value.setData(data.kline);
        } else {
            initChart(data.kline);
        }
        chart.value.timeScale().fitContent();
    } catch (error) {
        console.error('Error fetching stock data:', error);
    }
};

const fetchIntelligentAnalysisData = async () => {
    if (!searchSymbol.value) return;
    isFetchingIntelligentAnalysis.value = true;
    try {
        const response = await fetch(`${API_BASE_URL}/api/intelligent_analysis/${searchSymbol.value}`);
        if (!response.ok) throw new Error('Failed to fetch intelligent analysis');
        intelligentAnalysis.value = await response.json();
    } catch (error) {
        console.error('Error fetching intelligent analysis:', error);
        intelligentAnalysis.value = { logic: '获取失败', emotion: '获取失败', score: 0 };
    } finally {
        isFetchingIntelligentAnalysis.value = false;
    }
};

const initChart = (klineData) => {
    const chartContainer = document.getElementById('chart-container');
    if (!chartContainer) return;
    chart.value = createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 400,
        layout: {
            backgroundColor: '#ffffff',
            textColor: 'rgba(33, 56, 77, 1)',
        },
        grid: {
            vertLines: { color: 'rgba(197, 203, 206, 0.5)' },
            horzLines: { color: 'rgba(197, 203, 206, 0.5)' },
        },
        crosshair: { mode: 0 },
        rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.8)' },
        timeScale: { borderColor: 'rgba(197, 203, 206, 0.8)' },
    });
    candleSeries.value = chart.value.addCandlestickSeries({
        upColor: 'rgba(5, 150, 105, 1)',
        downColor: 'rgba(246, 53, 63, 1)',
        borderDownColor: 'rgba(246, 53, 63, 1)',
        borderUpColor: 'rgba(5, 150, 105, 1)',
        wickDownColor: 'rgba(246, 53, 63, 1)',
        wickUpColor: 'rgba(5, 150, 105, 1)',
    });
    candleSeries.value.setData(klineData);
};

const changeSymbol = () => {
    fetchStockData();
    fetchIntelligentAnalysisData();
};

const changeInterval = (interval) => {
    selectedInterval.value = interval;
    fetchStockData();
};

onMounted(() => {
    fetchStockData();
    fetchIntelligentAnalysisData();
});

</script>

<style scoped>
/* Market Analysis Styles */
.analysis-grid { display: flex; flex-direction: column; height: 100%; gap: 16px; }
.analysis-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
.search-bar { display: flex; gap: 8px; }
.search-bar input { padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 6px; font-size: 14px; }
.search-bar button { padding: 8px 16px; background-color: var(--accent-color); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.stock-info { display: flex; align-items: baseline; gap: 16px; }
.stock-name h2 { margin: 0; font-size: 24px; }
.stock-name span { font-size: 14px; color: var(--text-color-secondary); }
.stock-price { font-size: 28px; font-weight: 600; }
.stock-change { display: flex; flex-direction: column; font-size: 14px; }
.interval-tabs { display: flex; }
.interval-tabs button { padding: 6px 12px; border: 1px solid var(--border-color); background-color: transparent; cursor: pointer; font-size: 14px; border-radius: 4px; margin-right: 8px; }
.interval-tabs button.active { background-color: var(--accent-color-light); color: var(--accent-color); border-color: var(--accent-color); }
#chart-container { width: 100%; flex-grow: 1; min-height: 300px; }

/* Intelligence Styles */
#intelligence-container { border: 1px solid var(--border-color); border-radius: 8px; background-color: #fff; margin-top: 16px; }
.intelligence-header { padding: 12px 16px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); }
.intelligence-header h3 { margin: 0; font-size: 16px; }
.intelligence-content-wrapper { padding: 16px; }
.intelligence-content { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }
.intelligence-column { padding: 16px; border-radius: 6px; }
.logic-column { background-color: var(--accent-color-light); }
.emotion-column { transition: background-color 0.3s; }
.intelligence-column h4 { margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; margin-bottom: 8px; }
.pulse-dashboard { margin-bottom: 16px; }
.pulse-bar-container { width: 100%; background-color: var(--price-down-color); border-radius: 4px; overflow: hidden; }
.pulse-bar { height: 10px; background-color: var(--price-up-color); transition: width 0.5s; }
.pulse-labels { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-color-secondary); margin-top: 4px; }
.pulse-score { text-align: center; margin-top: 8px; font-weight: 600; }
</style>