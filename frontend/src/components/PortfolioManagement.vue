<template>
  <div class="portfolio-view">
      <div class="portfolio-card">
          <h3>我的持仓</h3>
          <table class="positions-table">
              <thead>
                  <tr>
                      <th>股票代码</th>
                      <th>持仓数量</th>
                      <th>成本单价</th>
                      <th>操作</th>
                  </tr>
              </thead>
              <tbody>
                  <tr v-for="pos in positions" :key="pos.record_id">
                      <td>{{ pos.fields['股票代码'] }}</td>
                      <td>{{ pos.fields['持仓数量'] }}</td>
                      <td>{{ pos.fields['成本单价'] }}</td>
                      <td>
                          <button @click="deletePosition(pos.record_id)" class="delete-btn">&times;</button>
                      </td>
                  </tr>
              </tbody>
          </table>
      </div>
      <div class="portfolio-card">
          <h3>添加新持仓</h3>
          <form @submit.prevent="addPosition" class="add-position-form">
              <div class="form-group">
                  <label>股票代码</label>
                  <input type="text" v-model="newPosition.symbol" required>
              </div>
              <div class="form-group">
                  <label>持仓数量</label>
                  <input type="number" v-model.number="newPosition.quantity" required>
              </div>
              <div class="form-group">
                  <label>成本单价</label>
                  <input type="number" step="0.01" v-model.number="newPosition.cost" required>
              </div>
              <button type="submit" class="strategy-btn">添加</button>
          </form>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const API_BASE_URL = 'http://127.0.0.1:8000';

const positions = ref([]);
const newPosition = ref({
    symbol: '',
    quantity: null,
    cost: null
});

const fetchPositions = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/positions`);
        if (!response.ok) throw new Error('Failed to fetch positions');
        positions.value = await response.json();
    } catch (error) {
        console.error('Error fetching positions:', error);
        alert('获取持仓列表失败，请查看控制台。');
    }
};

const addPosition = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/positions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                '股票代码': newPosition.value.symbol,
                '持仓数量': newPosition.value.quantity,
                '成本单价': newPosition.value.cost,
            }),
        });
        if (!response.ok) throw new Error('Failed to add position');
        const addedPosition = await response.json();
        positions.value.push(addedPosition);
        newPosition.value = { symbol: '', quantity: null, cost: null };
    } catch (error) {
        console.error('Error adding position:', error);
        alert('添加持仓失败，请检查输入或查看控制台。');
    }
};

const deletePosition = async (recordId) => {
    if (!confirm('确定要删除这条持仓记录吗？')) return;
    try {
        const response = await fetch(`${API_BASE_URL}/api/positions/${recordId}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to delete position');
        positions.value = positions.value.filter(p => p.record_id !== recordId);
    } catch (error) {
        console.error('Error deleting position:', error);
        alert('删除持仓失败，请查看控制台。');
    }
};

onMounted(() => {
    fetchPositions();
});
</script>

<style scoped>
.portfolio-view { display: flex; flex-direction: column; gap: 24px; }
.portfolio-card { background-color: var(--content-bg); border-radius: 8px; padding: 20px; border: 1px solid var(--border-color); }
.portfolio-card h3 { margin-top: 0; }
.positions-table { width: 100%; border-collapse: collapse; }
.positions-table th, .positions-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid var(--border-color); }
.positions-table th { background-color: #f9fafb; font-weight: 500; font-size: 12px; color: var(--text-color-secondary); text-transform: uppercase; }
.positions-table td .delete-btn { background: none; border: none; color: var(--price-down-color); cursor: pointer; font-size: 16px; }
.add-position-form { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; }
.add-position-form .form-group { flex-grow: 1; margin-bottom: 0; min-width: 120px; }
.strategy-btn { padding: 8px 16px; background-color: var(--accent-color); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
</style>