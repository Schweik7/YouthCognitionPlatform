import { createApp } from 'vue';
import ElementPlus from 'element-plus';
// 直接导入ElementPlus的CSS
import 'element-plus/dist/index.css';
// 导入ElementPlus图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
// 导入jsPsych的CSS
import 'jspsych/css/jspsych.css';
// 导入数字格式化样式
import './styles/numberFormat.css';
import App from './App.vue';
import { createRouter, createWebHistory } from 'vue-router';
import ReadingExperiment from './components/ReadingExperiment.vue';
import AttentionExperiment from './components/AttentionExperiment.vue';
import CalculationExperiment from './components/CalculationExperiment.vue';
import ReadingFluencyTest from './components/reading/ReadingFluencyTest.vue';
import OralReadingFluencyTest from './components/oral-reading/OralReadingFluencyTest.vue';
import LiteracyTest from './components/literacy/LiteracyTest.vue';
import RavenExperiment from './components/RavenExperiment.vue';
import UserInfo from './components/UserInfo.vue';
import TestSelection from './components/TestSelection.vue';

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: UserInfo },
    { path: '/selection', component: TestSelection },
    { path: '/experiment', component: ReadingExperiment },
    { path: '/attention-experiment', component: AttentionExperiment },
    { path: '/calculation-experiment', component: CalculationExperiment },
    { path: '/reading-fluency-test', component: ReadingFluencyTest },
    { path: '/oral-reading-fluency-test', component: OralReadingFluencyTest },
    { path: '/literacy-test', component: LiteracyTest },
    { path: '/raven-test', component: RavenExperiment }
  ]
});

router.beforeEach((to, from, next) => {
  // 如果访问的不是登录页面，检查是否已登录
  if (to.path !== '/' && to.path !== '/login') {
    const userInfo = localStorage.getItem('userInfo');
    if (!userInfo) {
      // 未登录，重定向到登录页
      next('/');
      return;
    }
  }
  next();
});
// 创建Vue应用
const app = createApp(App);

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// 注册全局组件和插件
app.use(ElementPlus);
app.use(router);

// 挂载应用
app.mount('#app');