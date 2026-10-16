<template>
  <div v-if="isFullscreen" class="fullscreen-page">
    <router-view />
    <ToastHost />
  </div>
  <div v-else class="shell">
    <!-- 桌面侧边栏 -->
    <aside class="sidebar">
      <div class="logo">🏠 个人工作生活</div>
      <nav class="side-nav">
        <router-link v-for="item in sideItems" :key="item.to" :to="item.to" class="side-item"
          :class="{ active: isActive(item) }">
          <span class="side-icon">{{ item.icon }}</span>{{ item.label }}
        </router-link>
      </nav>
      <div class="side-foot">v1.0 · 本地运行</div>
    </aside>

    <!-- 主内容 -->
    <main class="main">
      <router-view />
    </main>

    <!-- 移动端底部 Tab -->
    <nav class="tabbar">
      <router-link v-for="item in tabItems" :key="item.tab" :to="item.to" class="tab-item"
        :class="{ active: currentTab === item.tab }">
        <span class="tab-icon">{{ item.icon }}</span>
        <span class="tab-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <ToastHost />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ToastHost from './components/ToastHost.vue'

const route = useRoute()

const isFullscreen = computed(() => !!route.meta.fullscreen)

const sideItems = [
  { to: '/', label: '首页', icon: '🏠', tab: 'home' },
  { to: '/today', label: '今日计划', icon: '📅', tab: 'today' },
  { to: '/dev', label: '开发工作', icon: '💻', tab: 'dev' },
  { to: '/fitness', label: '健身计划', icon: '💪', tab: 'health' },
  { to: '/diet', label: '饮食计划', icon: '🥗', tab: 'health' },
  { to: '/entertainment', label: '游戏娱乐', icon: '🎮', tab: 'more' },
  { to: '/settings', label: '数据与设置', icon: '⚙️', tab: 'more' },
]

const tabItems = [
  { to: '/', label: '首页', icon: '🏠', tab: 'home' },
  { to: '/today', label: '今日', icon: '📅', tab: 'today' },
  { to: '/dev', label: '开发', icon: '💻', tab: 'dev' },
  { to: '/fitness', label: '健康', icon: '💪', tab: 'health' },
  { to: '/more', label: '更多', icon: '☰', tab: 'more' },
]

const currentTab = computed(() => route.meta.tab || '')

function isActive(item) {
  if (item.tab === 'home') return route.path === '/' || route.path === '/memos'
  return currentTab.value === item.tab && route.path === item.to
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
}

/* ---- 桌面侧栏 ---- */
.sidebar {
  display: none;
}

@media (min-width: 768px) {
  .sidebar {
    display: flex;
    flex-direction: column;
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: var(--sidebar-w);
    background: var(--c-card);
    border-right: 1px solid var(--c-line);
    padding: var(--sp-4) var(--sp-3);
    z-index: 10;
  }

  .main {
    margin-left: var(--sidebar-w);
  }
}

.logo {
  font-size: var(--fs-lg);
  font-weight: 600;
  padding: var(--sp-2) var(--sp-2) var(--sp-4);
}

.side-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.side-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 10px 12px;
  border-radius: var(--r-md);
  color: var(--c-text-2);
  font-size: var(--fs-md);
}

.side-item:hover {
  background: var(--c-bg);
}

.side-item.active {
  background: var(--c-primary-weak);
  color: var(--c-primary);
  font-weight: 500;
}

.side-icon {
  font-size: 17px;
}

.side-foot {
  font-size: var(--fs-xs);
  color: var(--c-text-3);
  padding: var(--sp-2);
}

/* ---- 移动端底部 Tab ---- */
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: calc(var(--tabbar-h) + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: var(--c-card);
  border-top: 1px solid var(--c-line);
  display: flex;
  z-index: 10;
}

@media (min-width: 768px) {
  .tabbar {
    display: none;
  }
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--c-text-3);
  font-size: var(--fs-xs);
}

.tab-item.active {
  color: var(--c-primary);
}

.tab-icon {
  font-size: 20px;
  line-height: 1;
}

.fullscreen-page {
  min-height: 100vh;
}
</style>
