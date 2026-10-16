<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-mask" @click.self="$emit('close')">
        <div class="modal-panel" :class="{ fullscreen }">
          <div class="modal-head">
            <h3>{{ title }}</h3>
            <button class="modal-x" @click="$emit('close')">✕</button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: Boolean,
  title: { type: String, default: '' },
  fullscreen: Boolean, // 训练模式等全屏场景
})
defineEmits(['close'])
</script>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 35, 41, 0.45);
  z-index: 100;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.modal-panel {
  background: var(--c-card);
  width: 100%;
  max-width: 560px;
  max-height: 88vh;
  border-radius: var(--r-lg) var(--r-lg) 0 0;
  display: flex;
  flex-direction: column;
  padding-bottom: env(safe-area-inset-bottom);
}

.modal-panel.fullscreen {
  max-width: none;
  height: 100%;
  max-height: none;
  border-radius: 0;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--sp-4);
  border-bottom: 1px solid var(--c-line);
}

.modal-head h3 {
  font-size: var(--fs-lg);
}

.modal-x {
  font-size: var(--fs-lg);
  color: var(--c-text-3);
  padding: 4px 8px;
}

.modal-body {
  padding: var(--sp-4);
  overflow-y: auto;
}

/* 桌面居中弹层 */
@media (min-width: 768px) {
  .modal-mask {
    align-items: center;
  }
  .modal-panel {
    border-radius: var(--r-lg);
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}
.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition: transform 0.18s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-panel,
.modal-leave-to .modal-panel {
  transform: translateY(24px);
}
@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal-panel,
  .modal-leave-active .modal-panel {
    transition: none;
  }
}
</style>
