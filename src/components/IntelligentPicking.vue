<template>
  <div class="portfolio-view">
      <div class="portfolio-card">
          <h3>智能选股</h3>
          <div style="margin-bottom: 20px;">
              <button @click="runPresetScreener('low_pe_high_roe')" :disabled="screenerLoading" class="run-backtest-btn" style="width: auto;">
                  <span v-if="screenerLoading">运行中...</span>
                  <span v-else>一键运行：低估值蓝筹</span>
              </button>
          </div>
          <!-- DIY Screener -->
          <div class="diy-screener">
              <h4>自定义筛选</h4>
              <div class="form-grid">
                  <div class="form-group">
                      <label>PE (市盈率) 范围</label>
                      <div class="input-group">
                          <input type="number" v-model.number="customScreenerRules.pe_ratio_min" placeholder="最小PE">
                          <span>-</span>
                          <input type="number" v-model.number="customScreenerRules.pe_ratio_max" placeholder="最大PE">
                      </div>
                  </div>
                  <div class="form-group">
                      <label>ROE (净资产收益率) > </label>
                      <input type="number" v-model.number="customScreenerRules.roe_min" placeholder="最小ROE (%)">
                  </div>
                  <div class="form-group">
                      <label>总市值 (亿) 范围</label>
                      <div class="input-group">
                          <input type="number" v-model.number="customScreenerRules.market_cap_min" placeholder="最小市值">
                          <span>-</span>
                          <input type="number" v-model.number="customScreenerRules.market_cap_max" placeholder="最大市值">
                      </div>
                  </div>
              </div>
              <button @click="runCustomScreener" :disabled="screenerLoading" class="strategy-btn secondary-btn">
                  <span v-if="screenerLoading">运行中...</span>
                  <span v-else>执行自定义筛选</span>
              </button>
          </div>
          <!-- NLP Screener -->
          <div class="nlp-screener" style="margin-top: 20px;">
              <h4>自然语言选股 (Beta)</h4>
              <div class="input-group">
                  <input type="text" v-model="nlpQuery" @keyup.enter="runNLPScreener" placeholder="例如：市值小于50亿，PE大于10">
                  <button @click="runNLPScreener" :disabled="screenerLoading" class="strategy-btn">
                      <span v-if="screenerLoading">分析中...</span>
                      <span v-else>发送</span>
                  </button>
              </div>
          </div>
          <table class="positions-table">
              <thead>
                  <tr>
                      <th>代码</th>
                      <th>名称</th>
                      <th>PE (动态)</th>
                      <th>ROE (%)</th>
                      <th>市值 (亿)</th>
                  </tr>
              </thead>
              <tbody>
                  <tr v-if="screenerLoading">
                      <td colspan="5" style="text-align: center; color: var(--text-color-secondary); padding: 20px;">正在从数千只股票中为您筛选...</td>
                  </tr>
                  <tr v-for="stock in screenerResults" :key="stock.代码">
                      <td>{{ stock.代码 }}</td>
                      <td>{{ stock.名称 }}</td>
                      <td>{{ stock.pe_ratio ? stock.pe_ratio.toFixed(2) : 'N/A' }}</td>
                      <td>{{ stock.roe ? stock.roe.toFixed(2) : 'N/A' }}</td>
                      <td>{{ stock.market_cap ? (stock.market_cap / 100000000).toFixed(2) : 'N/A' }}</td>
                  </tr>
                  <tr v-if="!screenerLoading && screenerResults.length === 0">
                      <td colspan="5" style="text-align: center; color: var(--text-color-secondary); padding: 20px;">暂无数据，请运行策略。</td>
                  </tr>
              </tbody>
          </table>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const API_BASE_URL = 'http://127.0.0.1:8000';

const screenerResults = ref([]);
const screenerLoading = ref(false);
const customScreenerRules = ref({
    pe_ratio_max: null,
    pe_ratio_min: 0,
    roe_min: null,
    market_cap_min: null,
    market_cap_max: null
});
const nlpQuery = ref('');

const runPresetScreener = async (presetName) => {
    screenerLoading.value = true;
    screenerResults.value = [];
    try {
        const response = await fetch(`${API_BASE_URL}/api/screen_stocks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preset: presetName })
        });
        if (!response.ok) { throw new Error('Failed to run screener'); }
        screenerResults.value = await response.json();
    } catch (error) {
        console.error('Error running screener:', error);
        alert('智能选股失败，请查看控制台获取详情。');
    } finally { screenerLoading.value = false; }
};

const runCustomScreener = async () => {
    screenerLoading.value = true;
    screenerResults.value = [];
    try {
        const response = await fetch(`${API_BASE_URL}/api/screen_stocks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ custom_rules: customScreenerRules.value })
        });
        if (!response.ok) { throw new Error('Failed to run custom screener'); }
        screenerResults.value = await response.json();
    } catch (error) {
        console.error('Error running custom screener:', error);
        alert('自定义选股失败，请查看控制台获取详情。');
    } finally { screenerLoading.value = false; }
};

const runNLPScreener = async () => {
    if (!nlpQuery.value) return;
    screenerLoading.value = true;
    screenerResults.value = [];
    try {
        const response = await fetch(`${API_BASE_URL}/api/screen_stocks_nlp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: nlpQuery.value })
        });
        if (!response.ok) { throw new Error('Failed to run NLP screener'); }
        screenerResults.value = await response.json();
    } catch (error) {
        console.error('Error running NLP screener:', error);
        alert('自然语言选股失败，请查看控制台获取详情。');
    } finally { screenerLoading.value = false; }
};

</script>

<style scoped>
.portfolio-view { display: flex; flex-direction: column; gap: 24px; }
.portfolio-card { background-color: var(--content-bg); border-radius: 8px; padding: 20px; border: 1px solid var(--border-color); }
.portfolio-card h3 { margin-top: 0; }
.diy-screener, .nlp-screener { margin-top: 20px; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px; }
.input-group { display: flex; align-items: center; gap: 8px; }
.input-group input { flex-grow: 1; }
.run-backtest-btn { width: 100%; padding: 10px; background-color: var(--accent-color); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
.strategy-btn { padding: 8px 16px; background-color: var(--accent-color); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.strategy-btn.secondary-btn { background-color: #4B5563; }
.positions-table { width: 100%; border-collapse: collapse; }
.positions-table th, .positions-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid var(--border-color); }
.positions-table th { background-color: #f9fafb; font-weight: 500; font-size: 12px; color: var(--text-color-secondary); text-transform: uppercase; }
</style>
