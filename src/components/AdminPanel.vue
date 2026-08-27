<template>
  <div class="admin-page">
    <div class="admin-container">
    <el-card>
      <template #header>
        <div class="header">
          <div class="header-title">
            <span class="header-mark"></span>
            <h2>测试结果后台管理</h2>
          </div>
          <div class="header-actions">
            <span class="admin-user" v-if="adminName">管理员：{{ adminName }}</span>
            <el-button text @click="goHome">返回首页</el-button>
            <el-button text type="danger" @click="logout">退出登录</el-button>
          </div>
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
          <el-radio-group v-model="scope" size="small">
            <el-radio-button label="summary">仅记录表</el-radio-button>
            <el-radio-button label="detail">含明细宽表</el-radio-button>
          </el-radio-group>
          <el-button type="success" size="small" @click="download({ testType: 'all' })">下载全部</el-button>
          <el-button size="small" @click="download({ testType: activeTab })" v-if="activeTab">下载当前测试</el-button>
          <el-button
            type="primary"
            size="small"
            v-if="activeTab && selectedCount"
            @click="download({ testType: activeTab, selected: true })"
          >下载选中({{ selectedCount }})</el-button>
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
          <el-table
            :data="tests[key].rows"
            border stripe max-height="520" size="small"
            row-key="__test_id__"
            @selection-change="(rows) => onSelectionChange(key, rows)"
          >
            <el-table-column type="selection" width="42" reserve-selection />
            <!-- 统一表头：用户信息 / 测试信息 / 任务指标信息 -->
            <el-table-column
              v-for="group in tests[key].column_groups"
              :key="group.label"
              :label="group.label"
              align="center"
            >
              <el-table-column
                v-for="col in group.columns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="110"
                show-overflow-tooltip
              />
            </el-table-column>
            <el-table-column label="操作" width="170" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openDetail(key, row)">
                  查看明细
                </el-button>
                <el-button
                  v-if="key === 'oral_reading_fluency' || key === 'literacy'"
                  type="primary" link size="small"
                  @click="openRecordings(key, row)"
                >
                  查看录音
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="暂无数据，请调整筛选条件后查询" />
    </el-card>

    <!-- 录音查看 / 在线评分 -->
    <el-dialog v-model="recDialog" :title="recTitle" width="920px" top="5vh">
      <div v-loading="recLoading">
        <div class="rec-toolbar">
          <span v-if="recData">
            考生：{{ recData.user.name }}（{{ recData.user.school }} {{ recData.user.grade }}年级{{ recData.user.class_number }}班）
            · 共 {{ recData.total }} 条录音
          </span>
          <el-button type="success" size="small" :disabled="!recData || !recData.total" @click="downloadAllAudio">
            下载全部录音(ZIP)
          </el-button>
        </div>

        <div class="rec-body" v-if="recData">
          <!-- 左侧：录音条目 + 播放器 -->
          <div class="rec-items">
            <el-table :data="recData.items" border size="small" max-height="60vh">
              <el-table-column prop="title" label="题目" width="120" />
              <el-table-column prop="stimulus" label="内容" min-width="160" show-overflow-tooltip />
              <el-table-column label="播放" min-width="240">
                <template #default="{ row }">
                  <audio v-if="row.has_file" controls preload="none" :src="authUrl(row.audio_url)" style="width: 100%; height: 32px;"></audio>
                  <span v-else class="muted">无录音</span>
                </template>
              </el-table-column>
              <el-table-column label="评测" width="110">
                <template #default="{ row }">
                  <span v-if="row.is_correct === true" class="ok">正确</span>
                  <span v-else-if="row.is_correct === false" class="bad">错误</span>
                  <span v-else-if="row.total_score != null">{{ row.total_score }}</span>
                  <span v-else class="muted">{{ row.evaluation_status }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 右侧：全量题目参考 -->
          <div class="rec-questions">
            <div class="rec-questions-title">全部题目</div>
            <ol>
              <li v-for="(q, i) in recData.questions" :key="i">{{ q }}</li>
            </ol>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 明细：具体操作数据 -->
    <el-dialog v-model="detailDialog" :title="detailTitle" width="900px" top="6vh">
      <div v-loading="detailLoading">
        <div class="rec-toolbar" v-if="detailData">
          <span>
            考生：{{ detailData.user.name }}（{{ detailData.user.school }}
            {{ detailData.user.grade }}年级{{ detailData.user.class_number }}班）
            · 共 {{ detailData.total }} 条明细
          </span>
        </div>
        <el-table
          v-if="detailData"
          :data="detailData.rows"
          border stripe size="small" max-height="65vh"
        >
          <el-table-column type="index" label="#" width="50" />
          <el-table-column
            v-for="col in detailData.columns"
            :key="col"
            :prop="col"
            :label="col"
            min-width="90"
            show-overflow-tooltip
          />
        </el-table>
        <el-empty v-if="detailData && !detailData.rows.length" description="该测试暂无明细数据" />
      </div>
    </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

const router = useRouter();

// ----- 管理员登录态 -----
const adminToken = ref(localStorage.getItem('adminToken') || '');
const adminName = ref(localStorage.getItem('adminName') || '');

const clearAuth = () => {
  adminToken.value = '';
  localStorage.removeItem('adminToken');
  localStorage.removeItem('adminName');
};

const logout = () => {
  clearAuth();
  router.push('/');
};

// 带令牌的请求（后台接口都需要）
const authFetch = async (url, options = {}) => {
  const response = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), Authorization: `Bearer ${adminToken.value}` }
  });
  if (response.status === 401) {
    clearAuth();
    ElMessage.error('登录已过期，请重新登录');
    router.push('/');
    throw new Error('未登录');
  }
  return response;
};

// 浏览器直接打开的链接（下载 / 音频）带不了请求头，改用 token 查询参数
const authUrl = (url) => `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(adminToken.value)}`;

const dateRange = ref([]);
const school = ref('');
const name = ref('');
const format = ref('xlsx');
const scope = ref('summary');
const loading = ref(false);

// 各测试类型当前勾选的会话 ID
const selections = reactive({});
const selectedCount = computed(() => (selections[activeTab.value] || []).length);
const onSelectionChange = (key, rows) => {
  selections[key] = rows.map((r) => r.__test_id__);
};

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
    const response = await authFetch(`/api/admin/results?${params.toString()}`);
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

// ----- 录音查看 -----
const recDialog = ref(false);
const recLoading = ref(false);
const recData = ref(null);
const recTitle = ref('录音查看');
const recCtx = ref({ test: '', testId: null });

const openRecordings = async (key, row) => {
  const test = key === 'oral_reading_fluency' ? 'oral' : 'literacy';
  const testId = row.__test_id__;
  recCtx.value = { test, testId };
  recTitle.value = `${tests[key].label} - 录音查看 / 在线评分`;
  recDialog.value = true;
  recLoading.value = true;
  recData.value = null;
  try {
    const response = await authFetch(`/api/admin/audio/recordings?test=${test}&test_id=${testId}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || '获取录音失败');
    }
    recData.value = await response.json();
  } catch (e) {
    ElMessage.error(e.message || '获取录音失败');
  } finally {
    recLoading.value = false;
  }
};

// ----- 明细查看 -----
const detailDialog = ref(false);
const detailLoading = ref(false);
const detailData = ref(null);
const detailTitle = ref('明细');

const openDetail = async (key, row) => {
  detailTitle.value = `${tests[key].label} - 具体操作明细`;
  detailDialog.value = true;
  detailLoading.value = true;
  detailData.value = null;
  try {
    const response = await authFetch(`/api/admin/detail?test_type=${key}&test_id=${row.__test_id__}`);
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || '获取明细失败');
    }
    detailData.value = await response.json();
  } catch (e) {
    ElMessage.error(e.message || '获取明细失败');
  } finally {
    detailLoading.value = false;
  }
};

const downloadAllAudio = () => {
  const { test, testId } = recCtx.value;
  const url = authUrl(`/api/admin/audio/download-all?test=${test}&test_id=${testId}`);
  const a = document.createElement('a');
  a.href = url;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

const download = ({ testType = 'all', selected = false } = {}) => {
  const params = buildParams();
  params.append('format', format.value);
  params.append('scope', scope.value);
  params.append('test_type', testType || 'all');
  if (selected && testType && testType !== 'all') {
    const ids = selections[testType] || [];
    if (!ids.length) {
      ElMessage.warning('请先勾选要下载的记录');
      return;
    }
    params.append('ids', ids.join(','));
  }
  const url = authUrl(`/api/admin/export?${params.toString()}`);
  // 触发浏览器下载
  const a = document.createElement('a');
  a.href = url;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

onMounted(() => {
  // 未登录直接回到封面页，由封面页的「后台登录」入口进入
  if (!adminToken.value) {
    ElMessage.warning('请先登录后台');
    router.push('/');
    return;
  }
  fetchResults();
});
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background:
    radial-gradient(1100px 520px at 12% -10%, rgba(76, 111, 255, .10), transparent 60%),
    radial-gradient(900px 460px at 96% 2%, rgba(18, 179, 168, .08), transparent 58%),
    var(--canvas);
  padding: 1px 0 40px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-user {
  font-size: 13px;
  color: var(--text-muted, #7a8296);
  margin-right: 4px;
}

.admin-container {
  max-width: 1320px;
  margin: 28px auto;
  padding: 0 clamp(14px, 2vw, 22px);
}

.admin-container :deep(.el-card) {
  border-radius: var(--r-xl);
  box-shadow: var(--sh-md);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-mark {
  width: 5px;
  height: 22px;
  border-radius: var(--r-full);
  background: linear-gradient(180deg, var(--brand-400), var(--brand-600));
}

.header h2 {
  margin: 0;
  font-size: 20px;
}

/* 筛选区 */
.filter-form {
  margin-bottom: 14px;
  padding: 18px 20px 4px;
  background: var(--surface-alt);
  border: 1px solid var(--line-soft);
  border-radius: var(--r-lg);
}

.filter-form :deep(.el-form-item__label) {
  font-size: 13px;
  color: var(--ink-500);
}

/* 导出条 */
.export-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--brand-50), rgba(18, 179, 168, .05));
  border: 1px solid var(--brand-100);
  border-radius: var(--r-md);
  flex-wrap: wrap;
  gap: 10px;
}

.range-info {
  color: var(--ink-500);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.export-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 表格与分页 */
.admin-container :deep(.el-tabs__item) {
  font-weight: 600;
  color: var(--ink-500);
}

.admin-container :deep(.el-tabs__item.is-active) { color: var(--brand-600); }

.admin-container :deep(.el-table) {
  border-radius: var(--r-md);
  overflow: hidden;
  font-variant-numeric: tabular-nums;
}

/* 弹窗内容 */
.rec-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding: 12px 16px;
  background: var(--surface-alt);
  border-radius: var(--r-md);
  gap: 12px;
  flex-wrap: wrap;
  color: var(--ink-700);
  font-size: 14px;
}

.rec-body {
  display: flex;
  gap: 16px;
}

.rec-items {
  flex: 1 1 auto;
  min-width: 0;
}

.rec-questions {
  flex: 0 0 210px;
  border-left: 1px solid var(--line);
  padding-left: 14px;
  max-height: 60vh;
  overflow: auto;
}

.rec-questions-title {
  font-weight: 700;
  margin-bottom: 10px;
  color: var(--ink-900);
  font-size: 13px;
  letter-spacing: .04em;
}

.rec-questions ol {
  margin: 0;
  padding-left: 20px;
  line-height: 1.95;
  color: var(--ink-500);
  font-size: 13px;
}

.muted { color: var(--ink-300); }

.ok {
  color: var(--success);
  font-weight: 600;
}

.bad {
  color: var(--danger);
  font-weight: 600;
}

@media (max-width: 900px) {
  .rec-body { flex-direction: column; }
  .rec-questions { flex: none; border-left: none; padding-left: 0; border-top: 1px solid var(--line); padding-top: 12px; }
}
</style>
