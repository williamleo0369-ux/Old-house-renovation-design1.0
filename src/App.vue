<template>
  <div id="app">
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c.251.042.505.042.752 0L14.25 2.25c.251-.042.505-.042.752 0m-5.25 0V1.5c0-.414.336-.75.75-.75h3.5c.414 0 .75.336.75.75v1.604m-4.5 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0m-7.5 5.25h15m-15 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0M3 10.5v5.714c0 .828.672 1.5 1.5 1.5h3.5c.828 0 1.5-.672 1.5-1.5V10.5m-6 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0m15-5.25h-15m15 0c.251.042.505.042.752 0m0 0c.251.042.505.042.752 0M21 10.5v5.714c0 .828-.672 1.5-1.5 1.5h-3.5c-.828 0-1.5-.672-1.5-1.5V10.5m6 0c.251.042.505.042.752 0m0 0c.251.042.505.042.752 0" />
          </svg>
        </div>
        <span>智能投研平台</span>
      </div>
      <ul class="nav-menu">
        <li v-for="item in menuItems" :key="item.id" 
            :class="{ 'nav-item': true, 'active': currentView === item.id }"
            @click="changeView(item.id)">
          <a href="#">
            <span class="icon" v-html="item.icon"></span>
            <span>{{ item.name }}</span>
          </a>
        </li>
      </ul>
    </div>

    <div class="main-container">
      <div class="app-header">
        <h2>{{ currentViewName }}</h2>
      </div>
      <div class="main-content">
        <component :is="activeComponent" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import MarketAnalysis from './components/MarketAnalysis.vue';
import SingleStockBacktest from './components/SingleStockBacktest.vue';
import PortfolioManagement from './components/PortfolioManagement.vue';
import IntelligentPicking from './components/IntelligentPicking.vue';
import PlaceholderView from './components/PlaceholderView.vue';

// --- Global State ---
const currentView = ref('marketAnalysis');
const menuItems = ref([
    { id: 'marketAnalysis', name: '行情分析', icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-3.75-2.25M21 18v-6m-18 6h16.5a2.25 2.25 0 002.25-2.25V6a2.25 2.25 0 00-2.25-2.25H3.75A2.25 2.25 0 001.5 6v10.5A2.25 2.25 0 003.75 18z" /></svg>' },
    { id: 'singleStockBacktest', name: '单股回测', icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h12A2.25 2.25 0 0020.25 14.25V3M3.75 21h16.5M16.5 3.75h.008v.008h-.008V3.75z" /></svg>' },
    { id: 'portfolioManagement', name: '组合管理', icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a2.25 2.25 0 00-2.25-2.25H15a3 3 0 11-6 0H5.25A2.25 2.25 0 003 12m18 0v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6m18 0V9M3 12V9m18 0a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 9m18 0V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v3" /></svg>' },
    { id: 'intelligentPicking', name: '智能选股', icon: '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 21v-1.5M12 3v1.5m0 15v1.5m3.75-18v1.5m0 15v-1.5M5.625 6.375l-1.125-1.125M19.5 19.5l-1.125-1.125M18.375 5.625l-1.125 1.125M6.75 19.5l-1.125-1.125" /></svg>' },
]);

const components = {
  marketAnalysis: MarketAnalysis,
  singleStockBacktest: SingleStockBacktest,
  portfolioManagement: PortfolioManagement,
  intelligentPicking: IntelligentPicking,
};

const activeComponent = computed(() => components[currentView.value] || PlaceholderView);

const currentViewName = computed(() => menuItems.value.find(item => item.id === currentView.value)?.name || '市场总览');

const changeView = (viewId) => {
    currentView.value = viewId;
};

</script>

<style>
.sidebar {
    width: var(--sidebar-width);
    background-color: var(--sidebar-bg);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 20px 0;
    transition: width 0.3s;
    flex-shrink: 0;
    overflow-y: auto;
}

.sidebar-header {
    padding: 0 20px 20px 20px;
    font-size: 20px;
    font-weight: 600;
    display: flex;
    align-items: center;
}

.sidebar-header .logo {
    width: 32px;
    height: 32px;
    margin-right: 10px;
    background-color: var(--accent-color);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.sidebar-header .logo svg {
    width: 20px;
    height: 20px;
    stroke: white;
}

.nav-menu {
    list-style: none;
    padding: 0;
    margin: 0;
    flex-grow: 1;
}

.nav-item a {
    display: flex;
    align-items: center;
    padding: 12px 20px;
    text-decoration: none;
    color: var(--text-color-secondary);
    font-size: 15px;
    font-weight: 500;
    border-left: 3px solid transparent;
    transition: all 0.2s ease;
}

.nav-item a:hover {
    background-color: var(--bg-color);
}

.nav-item.active a {
    color: var(--accent-color);
    background-color: var(--accent-color-light);
    border-left-color: var(--accent-color);
}

.nav-item .icon {
    margin-right: 15px;
    width: 20px;
    height: 20px;
}

.main-container {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.app-header {
    height: var(--header-height);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    padding: 0 24px;
    flex-shrink: 0;
    background-color: var(--content-bg);
}

.app-header h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
}

.main-content {
    flex-grow: 1;
    padding: 24px;
    overflow-y: auto;
}

.price-up { color: var(--price-up-color); }
.price-down { color: var(--price-down-color); }

</style>
