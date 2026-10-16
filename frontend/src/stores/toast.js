// 全局 Toast：reactive 队列 + useToast 读取
import { reactive } from 'vue'

export const toastState = reactive({
  items: [], // { id, msg, type }
  _seq: 0,
})

export function showToast(msg, type = 'info', duration = 2200) {
  const id = ++toastState._seq
  toastState.items.push({ id, msg, type })
  setTimeout(() => {
    const i = toastState.items.findIndex((t) => t.id === id)
    if (i >= 0) toastState.items.splice(i, 1)
  }, duration)
}
