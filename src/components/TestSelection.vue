<template>
  <div class="test-selection-page page-shell">
    <TopNavBar />
    <div class="test-selection-container">
      <!-- 页面标题区 -->
      <header class="page-head">
        <span class="sec-eyebrow">STEP 2</span>
        <h1>中小学生学习困难筛查线上平台</h1>
        <p>请选择一个测试项目进行评估</p>
      </header>

      <!-- 测评模块网格 -->
      <div class="test-grid">
        <article
          v-for="test in availableTests"
          :key="test.id"
          class="test-card"
          :style="{ '--accent': test.accent, '--accent-soft': test.accentSoft }"
          tabindex="0"
          @click="selectTest(test)"
          @keyup.enter="selectTest(test)"
        >
          <div class="card-top">
            <div class="test-icon">
              <el-icon :size="26">
                <component :is="test.icon" />
              </el-icon>
            </div>
            <span class="card-index">{{ test.tag }}</span>
          </div>

          <h3>{{ test.name }}</h3>
          <p>{{ test.description }}</p>

          <div class="card-foot">
            <span class="go">
              <el-icon><ArrowRight /></el-icon>
            </span>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Document, View, EditPen, Microphone, ChatLineRound, Grid, ArrowRight } from '@element-plus/icons-vue';
import TopNavBar from './TopNavBar.vue';

const router = useRouter();

// 可用测试列表
const availableTests = ref([
  {
    id: 'reading-comprehension',
    name: '阅读流畅性测试',
    description: '测量阅读句子并判断真假的能力，考察您的阅读速度和理解能力',
    icon: 'Document',
    route: '/experiment',
    tag: '01',
    accent: 'var(--hue-reading)',
    accentSoft: 'rgba(76, 111, 255, .10)'
  },
  {
    id: 'reading-fluency',
    name: '朗读流畅性测试',
    description: '测量朗读汉字的流畅度，评估您的口语表达能力和字音准确性',
    icon: 'Microphone',
    route: '/oral-reading-fluency-test',
    tag: '02',
    accent: 'var(--hue-oral)',
    accentSoft: 'rgba(240, 116, 58, .10)'
  },
  {
    id: 'attention-test',
    name: '注意力筛查测试',
    description: '测量快速定位特定符号的能力，评估您的专注力和视觉搜索能力',
    icon: 'View',
    route: '/attention-experiment',
    tag: '03',
    accent: 'var(--hue-attention)',
    accentSoft: 'rgba(18, 179, 168, .10)'
  },
  {
    id: 'calculation-test',
    name: '计算流畅性测试',
    description: '测量快速计算数学题的能力，评估您的心算能力和数学流畅度',
    icon: 'EditPen',
    route: '/calculation-experiment',
    tag: '04',
    accent: 'var(--hue-calc)',
    accentSoft: 'rgba(139, 92, 246, .10)'
  },
  {
    id: 'literacy-test',
    name: '识字量测验',
    description: '测量汉字识别和朗读能力，评估您的识字水平和发音准确性',
    icon: 'ChatLineRound',
    route: '/literacy-test',
    tag: '05',
    accent: 'var(--hue-literacy)',
    accentSoft: 'rgba(224, 81, 140, .10)'
  },
  {
    id: 'raven-test',
    name: '图形推理测试',
    description: '瑞文智力测验，通过图形推理评估您的逻辑思维和抽象推理能力',
    icon: 'Grid',
    route: '/raven-test',
    tag: '06',
    accent: 'var(--hue-raven)',
    accentSoft: 'rgba(240, 169, 44, .10)'
  }
]);

onMounted(() => {
  // 检查登录状态
  const userInfoStr = localStorage.getItem('userInfo');
  if (!userInfoStr) {
    ElMessage.warning('未登录，请先登录');
    router.push('/');
    return;
  }
});

// 选择测试
const selectTest = (test) => {
  router.push(test.route);
};

</script>

<style scoped>
.test-selection-container {
  max-width: 1180px;
  margin: 0 auto;
  padding: clamp(28px, 4vw, 56px) clamp(18px, 3vw, 28px) clamp(48px, 6vw, 80px);
}

/* 标题区 */
.page-head {
  text-align: center;
  margin-bottom: clamp(28px, 4vw, 48px);
}

.page-head h1 {
  margin: 14px 0 10px;
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.3;
}

.page-head p {
  margin: 0;
  color: var(--ink-500);
  font-size: 15px;
}

/* 网格 */
.test-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(16px, 2vw, 24px);
}

/* 卡片 */
.test-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 26px 24px 20px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: var(--sh-xs);
  cursor: pointer;
  overflow: hidden;
  transition: transform .26s cubic-bezier(.22, .8, .3, 1),
              box-shadow .26s ease,
              border-color .26s ease;
}

/* 顶部彩条 */
.test-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: var(--accent);
  opacity: .85;
  transform: scaleX(.28);
  transform-origin: left;
  transition: transform .34s cubic-bezier(.22, .8, .3, 1);
}

/* 悬停时的背景晕染 */
.test-card::after {
  content: '';
  position: absolute;
  width: 220px;
  height: 220px;
  right: -80px;
  top: -90px;
  border-radius: 50%;
  background: var(--accent-soft);
  opacity: 0;
  transition: opacity .3s ease;
}

.test-card:hover,
.test-card:focus-visible {
  transform: translateY(-6px);
  box-shadow: var(--sh-lg);
  border-color: color-mix(in srgb, var(--accent) 32%, var(--line));
  outline: none;
}

.test-card:hover::before,
.test-card:focus-visible::before { transform: scaleX(1); }

.test-card:hover::after,
.test-card:focus-visible::after { opacity: 1; }

.card-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.test-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-md);
  background: var(--accent-soft);
  color: var(--accent);
  transition: transform .3s cubic-bezier(.22, .8, .3, 1);
}

.test-card:hover .test-icon { transform: scale(1.06) rotate(-4deg); }

.card-index {
  font-family: var(--font-num);
  font-size: 22px;
  font-weight: 800;
  color: var(--line);
  letter-spacing: .04em;
  transition: color .3s ease;
}

.test-card:hover .card-index { color: color-mix(in srgb, var(--accent) 38%, #ffffff); }

.test-card h3 {
  position: relative;
  z-index: 1;
  margin: 0 0 10px;
  font-size: 18px;
  letter-spacing: .01em;
}

.test-card p {
  position: relative;
  z-index: 1;
  margin: 0;
  flex-grow: 1;
  color: var(--ink-500);
  font-size: 13.5px;
  line-height: 1.75;
}

.card-foot {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px dashed var(--line-soft);
}

.go {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--surface-alt);
  color: var(--ink-300);
  transition: all .28s ease;
}

.test-card:hover .go {
  background: var(--accent);
  color: #fff;
  transform: translateX(4px);
}

@media (max-width: 1024px) {
  .test-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .test-grid { grid-template-columns: 1fr; }
}
</style>
