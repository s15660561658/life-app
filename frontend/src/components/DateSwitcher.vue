<template>
  <div class="date-switcher">
    <button class="ds-btn" aria-label="前一天" @click="$emit('change', addDays(date, -1))">‹</button>
    <button class="ds-label" @click="$emit('change', todayStr())">{{ label }}</button>
    <button class="ds-btn" aria-label="后一天" @click="$emit('change', addDays(date, 1))">›</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { addDays, formatDateCN, todayStr } from '../api'

const props = defineProps({
  date: { type: String, required: true },
})
defineEmits(['change'])

const label = computed(() => formatDateCN(props.date))
</script>

<style scoped>
.date-switcher {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.ds-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--r-full);
  background: var(--c-card);
  box-shadow: var(--shadow-card);
  font-size: var(--fs-lg);
  color: var(--c-text-2);
}

.ds-label {
  min-width: 150px;
  padding: 7px 12px;
  border-radius: var(--r-full);
  background: var(--c-card);
  box-shadow: var(--shadow-card);
  font-size: var(--fs-md);
  font-weight: 500;
}
</style>
