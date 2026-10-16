<template>
  <button class="checkbox" :class="{ checked: modelValue }" @click="$emit('update:modelValue', !modelValue)">
    <svg v-if="modelValue" viewBox="0 0 16 16" width="12" height="12">
      <path d="M3 8.5 6.5 12 13 4.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
  </button>
</template>

<script setup>
defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.checkbox {
  width: 20px;
  height: 20px;
  min-width: 20px;
  border-radius: var(--r-full);
  border: 2px solid var(--c-border);
  background: var(--c-card);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.12s;
}

.checkbox.checked {
  background: var(--c-success);
  border-color: var(--c-success);
}
</style>
