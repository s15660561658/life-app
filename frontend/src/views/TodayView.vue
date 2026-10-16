<template>
  <div class="page">
    <div class="row head">
      <h2 class="page-title grow">今日计划</h2>
      <button class="btn btn-primary" @click="openCreate">＋ 新建</button>
    </div>

    <div class="row toolbar">
      <DateSwitcher :date="date" @change="date = $event" />
      <span class="muted">{{ doneCount }}/{{ items.length }} 已完成</span>
    </div>

    <div class="progress" v-if="items.length">
      <div class="progress-bar" :style="{ width: progressPct + '%' }"></div>
    </div>

    <div v-if="alldayGroup.length" class="group">
      <div class="group-title muted">全天</div>
      <div v-for="t in alldayGroup" :key="t.id" class="task card" :class="{ done: t.done }">
        <Checkbox :model-value="t.done" @update:model-value="toggle(t)" />
        <div class="grow task-main">
          <div class="task-title">{{ t.title }}</div>
          <div v-if="t.note" class="muted">{{ t.note }}</div>
        </div>
        <button class="icon-btn" @click="openEdit(t)">✏️</button>
        <button class="icon-btn" @click="askDelete(t)">🗑️</button>
      </div>
    </div>

    <div v-if="timedGroup.length" class="group">
      <div class="group-title muted">有时间</div>
      <div v-for="t in timedGroup" :key="t.id" class="task card" :class="{ done: t.done }">
        <Checkbox :model-value="t.done" @update:model-value="toggle(t)" />
        <div class="task-time">{{ timeText(t) }}</div>
        <div class="grow task-main">
          <div class="task-title">{{ t.title }}</div>
          <div v-if="t.note" class="muted">{{ t.note }}</div>
        </div>
        <button class="icon-btn" @click="openEdit(t)">✏️</button>
        <button class="icon-btn" @click="askDelete(t)">🗑️</button>
      </div>
    </div>

    <EmptyState v-if="!items.length" text="这一天还没有任务" icon="📅" />

    <!-- 移动端悬浮新建按钮 -->
    <button class="fab" @click="openCreate">＋</button>

    <Modal :open="formOpen" :title="editing ? '编辑任务' : '新建任务'" @close="formOpen = false">
      <form @submit.prevent="submit">
        <div class="field">
          <label class="field-label">标题 *</label>
          <input v-model="form.title" class="input" placeholder="要做什么？" required maxlength="100" />
        </div>
        <div class="field">
          <label class="field-label">日期</label>
          <input v-model="form.date" type="date" class="input" required />
        </div>
        <div class="row">
          <div class="field grow">
            <label class="field-label">开始时间（可选）</label>
            <input v-model="form.start_time" type="time" class="input" />
          </div>
          <div class="field grow">
            <label class="field-label">结束时间（可选）</label>
            <input v-model="form.end_time" type="time" class="input" />
          </div>
        </div>
        <div class="field">
          <label class="field-label">备注</label>
          <textarea v-model="form.note" class="textarea" maxlength="300"></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="!!deleting" title="删除任务" :message="`确定删除「${deleting?.title}」吗？`"
      confirm-text="删除" danger @confirm="doDelete" @cancel="deleting = null" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api, todayStr } from '../api'
import Checkbox from '../components/Checkbox.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import DateSwitcher from '../components/DateSwitcher.vue'
import EmptyState from '../components/EmptyState.vue'
import Modal from '../components/Modal.vue'
import { showToast } from '../stores/toast'

const date = ref(todayStr())
const items = ref([])
const formOpen = ref(false)
const editing = ref(null)
const deleting = ref(null)
const form = ref({ title: '', date: todayStr(), start_time: '', end_time: '', note: '' })

const alldayGroup = computed(() => items.value.filter((t) => !t.start_time))
const timedGroup = computed(() => items.value.filter((t) => t.start_time))
const doneCount = computed(() => items.value.filter((t) => t.done).length)
const progressPct = computed(() =>
  items.value.length ? Math.round((doneCount.value / items.value.length) * 100) : 0)

async function load() {
  items.value = await api.get(`/tasks?date=${date.value}`)
}

watch(date, load)
onMounted(load)

function timeText(t) {
  if (t.start_time && t.end_time) return `${t.start_time}\n${t.end_time}`
  return t.start_time || ''
}

function openCreate() {
  editing.value = null
  form.value = { title: '', date: date.value, start_time: '', end_time: '', note: '' }
  formOpen.value = true
}

function openEdit(t) {
  editing.value = t
  form.value = {
    title: t.title,
    date: t.date,
    start_time: t.start_time || '',
    end_time: t.end_time || '',
    note: t.note || '',
  }
  formOpen.value = true
}

async function submit() {
  const body = {
    title: form.value.title.trim(),
    date: form.value.date,
    start_time: form.value.start_time || null,
    end_time: form.value.end_time || null,
    note: form.value.note.trim(),
  }
  if (!body.title) return
  if (editing.value) {
    await api.put(`/tasks/${editing.value.id}`, body)
    showToast('已保存', 'success')
  } else {
    await api.post('/tasks', body)
    showToast('已创建', 'success')
  }
  formOpen.value = false
  await load()
}

async function toggle(t) {
  await api.put(`/tasks/${t.id}`, { done: !t.done })
  await load()
}

function askDelete(t) {
  deleting.value = t
}

async function doDelete() {
  await api.del(`/tasks/${deleting.value.id}`)
  deleting.value = null
  showToast('已删除', 'success')
  await load()
}
</script>

<style scoped>
.head {
  margin-bottom: var(--sp-3);
}

.head .page-title {
  margin-bottom: 0;
}

.toolbar {
  margin-bottom: var(--sp-3);
}

.progress {
  height: 6px;
  background: var(--c-line);
  border-radius: var(--r-full);
  overflow: hidden;
  margin-bottom: var(--sp-4);
}

.progress-bar {
  height: 100%;
  background: var(--c-success);
  border-radius: var(--r-full);
  transition: width 0.2s ease;
}

.group {
  margin-bottom: var(--sp-4);
}

.group-title {
  margin-bottom: var(--sp-2);
  padding-left: var(--sp-1);
}

.task {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-2);
}

.task.done .task-title {
  text-decoration: line-through;
  color: var(--c-text-3);
}

.task-main {
  min-width: 0;
}

.task-title {
  font-size: var(--fs-md);
  word-break: break-word;
}

.task-time {
  font-size: var(--fs-sm);
  color: var(--c-text-2);
  white-space: pre-line;
  text-align: center;
  min-width: 44px;
  line-height: 1.4;
}

.icon-btn {
  font-size: 15px;
  padding: 4px;
  opacity: 0.7;
}

.icon-btn:hover {
  opacity: 1;
}

.fab {
  display: none;
}

@media (max-width: 767px) {
  .fab {
    display: flex;
    position: fixed;
    right: 20px;
    bottom: calc(var(--tabbar-h) + env(safe-area-inset-bottom) + 20px);
    width: 52px;
    height: 52px;
    border-radius: var(--r-full);
    background: var(--c-primary);
    color: #fff;
    font-size: 26px;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(79, 124, 255, 0.4);
    z-index: 20;
  }
}
</style>
