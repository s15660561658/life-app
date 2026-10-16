<template>
  <div class="empty">
    <div class="empty-icon">{{ icon }}</div>
    <p>{{ text }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '暂无数据' },
  icon: { type: String, default: '📭' },
})
</script>

<style scoped>
.empty {
  text-align: center;
  padding: 40px 16px;
  color: var(--c-text-3);
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.empty p {
  font-size: var(--fs-md);
}
</style>
