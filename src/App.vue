<template>
  <div class="app-container">
    <el-config-provider :locale="zhCn">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-config-provider>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import zhCn from 'element-plus/dist/locale/zh-cn.mjs';
</script>

<style>
.app-container {
  width: 100%;
  min-height: 100vh;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity .28s ease, transform .28s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
