<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="open" class="confirm-mask" @click.self="$emit('cancel')">
        <div class="confirm-box card">
          <h3>{{ title }}</h3>
          <p class="confirm-msg">{{ message }}</p>
          <div class="row confirm-actions">
            <button class="btn btn-plain grow" @click="$emit('cancel')">取消</button>
            <button class="btn grow" :class="danger ? 'btn-danger' : 'btn-primary'" @click="$emit('confirm')">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: Boolean,
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  danger: Boolean,
})
defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 35, 41, 0.45);
  z-index: 120;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-5);
}

.confirm-box {
  width: 100%;
  max-width: 340px;
  padding: var(--sp-5);
}

.confirm-box h3 {
  font-size: var(--fs-lg);
  margin-bottom: var(--sp-2);
}

.confirm-msg {
  color: var(--c-text-2);
  font-size: var(--fs-md);
  line-height: 1.6;
  margin-bottom: var(--sp-5);
  white-space: pre-line;
}

.confirm-actions .btn {
  margin: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.12s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
