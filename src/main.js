import { createApp } from 'vue';
import ElementPlus from 'element-plus';
// 直接导入ElementPlus的CSS
import 'element-plus/dist/index.css';
// 导入jsPsych的CSS
import 'jspsych/css/jspsych.css';
import App from './App.vue';
import { createRouter, createWebHistory } from 'vue-router';
import ReadingExperiment from './components/ReadingExperiment.vue';
import UserInfo from './components/UserInfo.vue';

// 创建路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: UserInfo },
    { path: '/experiment', component: ReadingExperiment }
  ]
});

// 创建Vue应用
const app = createApp(App);

// 注册全局组件和插件
app.use(ElementPlus);
app.use(router);

// 挂载应用
app.mount('#app');