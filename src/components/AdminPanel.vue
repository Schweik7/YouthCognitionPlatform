<template>
  <div class="admin-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>测试结果后台管理</h2>
          <el-button text @click="goHome">返回首页</el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="学校">
          <el-input v-model="school" placeholder="学校（模糊）" clearable />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="name" placeholder="姓名（模糊）" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchResults">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 导出 -->
      <div class="export-bar">
        <span class="range-info" v-if="rangeInfo">区间：{{ rangeInfo.start }} ~ {{ rangeInfo.end }}，共 {{ total }} 条</span>
        <div class="export-actions">
          <el-radio-group v-model="format" size="small">
            <el-radio-button label="xlsx">XLSX</el-radio-button>
            <el-radio-button label="csv">CSV</el-radio-button>
          </el-radio-group>
          <el-button type="success" size="small" @click="download('all')">下载全部</el-button>
          <el-button size="small" @click="download(activeTab)" v-if="activeTab">下载当前测试</el-button>
        </div>
      </div>

      <!-- 结果表格 -->
      <el-tabs v-model="activeTab" v-if="testKeys.length">
        <el-tab-pane
          v-for="key in testKeys"
          :key="key"
          :name="key"
          :label="`${tests[key].label} (${tests[key].rows.length})`"
        >
          <el-table :data="tests[key].rows" border stripe max-height="520" size="small">
            <el-table-column
              v-for="col in tests[key].columns"
              :key="col"
              :prop="col"
              :label="col"
              min-width="110"
              show-overflow-tooltip
            />
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="暂无数据，请调整筛选条件后查询" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

const router = useRouter();

const dateRange = ref([]);
const school = ref('');
const name = ref('');
const format = ref('xlsx');
const loading = ref(false);

const tests = reactive({});
const total = ref(0);
const rangeInfo = ref(null);
const activeTab = ref('');

const testKeys = computed(() => Object.keys(tests));

const goHome = () => router.push('/');

// 构建查询参数（不含导出相关）
const buildParams = () => {
  const params = new URLSearchParams();
  if (dateRange.value && dateRange.value.length === 2) {
    params.append('start_date', dateRange.value[0]);
    params.append('end_date', dateRange.value[1]);
  }
  if (school.value) params.append('school', school.value);
  if (name.value) params.append('name', name.value);
  return params;
};

const fetchResults = async () => {
  loading.value = true;
  try {
    const params = buildParams();
    const response = await fetch(`/api/admin/results?${params.toString()}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || '查询失败');
    }
    const data = await response.json();
    // 重置并填充
    Object.keys(tests).forEach((k) => delete tests[k]);
    Object.entries(data.tests).forEach(([k, v]) => { tests[k] = v; });
    total.value = data.total;
    rangeInfo.value = data.range;
    if (testKeys.value.length && !testKeys.value.includes(activeTab.value)) {
      activeTab.value = testKeys.value[0];
    }
  } catch (e) {
    ElMessage.error(e.message || '查询失败');
  } finally {
    loading.value = false;
  }
};

const download = (testType) => {
  const params = buildParams();
  params.append('format', format.value);
  params.append('test_type', testType || 'all');
  const url = `/api/admin/export?${params.toString()}`;
  // 触发浏览器下载
  const a = document.createElement('a');
  a.href = url;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

onMounted(fetchResults);
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 16px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-form {
  margin-bottom: 8px;
}
.export-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}
.range-info {
  color: #909399;
  font-size: 13px;
}
.export-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
