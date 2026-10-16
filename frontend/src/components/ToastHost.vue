<template>
  <Teleport to="body">
    <div class="toast-host">
      <TransitionGroup name="toast">
        <div v-for="t in toastState.items" :key="t.id" class="toast" :class="`toast-${t.type}`">
          {{ t.msg }}
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { toastState } from '../stores/toast'
</script>

<style scoped>
.toast-host {
  position: fixed;
  top: 16px;
  left: 0;
  right: 0;
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  padding: 0 16px;
}

.toast {
  background: rgba(31, 35, 41, 0.92);
  color: #fff;
  padding: 10px 18px;
  border-radius: var(--r-full);
  font-size: var(--fs-sm);
  max-width: 100%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
}

.toast-error {
  background: rgba(239, 68, 68, 0.95);
}

.toast-success {
  background: rgba(34, 197, 94, 0.95);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.18s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
