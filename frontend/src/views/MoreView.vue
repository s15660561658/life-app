<template>
  <div class="page">
    <h2 class="page-title">更多</h2>
    <router-link v-for="e in entries" :key="e.to" :to="e.to" class="card entry-card">
      <span class="entry-icon">{{ e.icon }}</span>
      <span class="grow">
        <span class="entry-title">{{ e.title }}</span>
        <span class="muted entry-desc">{{ e.desc }}</span>
      </span>
      <span class="entry-arrow">›</span>
    </router-link>
  </div>
</template>

<script setup>
const entries = [
  { to: '/entertainment', icon: '🎮', title: '游戏娱乐', desc: '游戏、电影、聚会等日程安排' },
  { to: '/settings', icon: '⚙️', title: '数据与设置', desc: '统计、备份恢复、偏好设置' },
  { to: '/memos', icon: '📝', title: '备忘录', desc: '随手记录想法与待办' },
]
</script>

<style scoped>
.entry-card {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4);
  margin-bottom: var(--sp-3);
  color: var(--c-text);
}

.entry-icon {
  font-size: 24px;
}

.entry-title {
  display: block;
  font-weight: 500;
}

.entry-desc {
  font-size: var(--fs-sm);
}

.entry-arrow {
  font-size: 20px;
  color: var(--c-text-3);
}
</style>
