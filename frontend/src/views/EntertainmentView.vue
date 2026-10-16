<template>
  <div class="page">
    <div class="row head">
      <h2 class="page-title grow">游戏娱乐</h2>
      <button class="btn btn-primary" @click="openCreate">＋ 新日程</button>
    </div>

    <!-- 待进行 -->
    <div class="group">
      <div class="group-title muted">待进行 · {{ upcoming.length }}</div>
      <div v-for="e in upcoming" :key="e.id" class="card event-card">
        <button class="done-btn" title="标记完成" @click="toggleDone(e)">✓</button>
        <div class="grow item-main">
          <div class="row">
            <span class="item-title">{{ e.title }}</span>
            <Tag :type="catColor(e.category)">{{ catLabel(e.category) }}</Tag>
          </div>
          <div class="muted item-time">🕐 {{ formatStart(e.start_at) }}</div>
          <div v-if="e.note" class="muted item-note">{{ e.note }}</div>
        </div>
        <button class="icon-btn" @click="openEdit(e)">✏️</button>
        <button class="icon-btn" @click="askDelete(e)">🗑️</button>
      </div>
      <EmptyState v-if="!upcoming.length" text="暂无待进行日程" icon="🎉" />
    </div>

    <!-- 已结束 -->
    <div class="group" v-if="past.length">
      <div class="group-title muted">已结束 · {{ past.length }}</div>
      <div v-for="e in past" :key="e.id" class="card event-card past">
        <div class="grow item-main">
          <div class="row">
            <span class="item-title">{{ e.title }}</span>
            <Tag :type="catColor(e.category)">{{ catLabel(e.category) }}</Tag>
            <Tag v-if="e.done" type="green">已完成</Tag>
            <Tag v-else type="gray">已过期</Tag>
          </div>
          <div class="muted item-time">🕐 {{ formatStart(e.start_at) }}</div>
          <div v-if="e.note" class="muted item-note">{{ e.note }}</div>
        </div>
        <button v-if="!e.done" class="btn btn-plain btn-sm" @click="toggleDone(e)">补标完成</button>
        <button class="icon-btn" @click="askDelete(e)">🗑️</button>
      </div>
    </div>

    <!-- 移动端悬浮新建按钮 -->
    <button class="fab" @click="openCreate">＋</button>

    <Modal :open="formOpen" :title="editing ? '编辑日程' : '新日程'" @close="formOpen = false">
      <form @submit.prevent="submit">
        <div class="field">
          <label class="field-label">标题 *</label>
          <input v-model="form.title" class="input" placeholder="做什么？" required maxlength="80" />
        </div>
        <div class="field">
          <label class="field-label">类型</label>
          <select v-model="form.category" class="select">
            <option v-for="c in CATS" :key="c.key" :value="c.key">{{ c.label }}</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">时间 *</label>
          <input v-model="form.startLocal" type="datetime-local" class="input" required />
        </div>
        <div class="field">
          <label class="field-label">备注</label>
          <textarea v-model="form.note" class="textarea" maxlength="200"></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="!!deleting" title="删除日程" :message="`确定删除「${deleting?.title}」吗？`"
      confirm-text="删除" danger @confirm="doDelete" @cancel="deleting = null" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import Modal from '../components/Modal.vue'
import Tag from '../components/Tag.vue'
import { showToast } from '../stores/toast'

const CATS = [
  { key: 'game', label: '🎮 游戏', color: 'blue' },
  { key: 'movie', label: '🎬 电影', color: 'purple' },
  { key: 'party', label: '🎉 聚会', color: 'orange' },
  { key: 'other', label: '📌 其他', color: 'gray' },
]

const upcoming = ref([])
const past = ref([])
const formOpen = ref(false)
const editing = ref(null)
const deleting = ref(null)
const form = ref({ title: '', category: 'game', startLocal: '', note: '' })

function catLabel(key) {
  return CATS.find((c) => c.key === key)?.label || key
}

function catColor(key) {
  return CATS.find((c) => c.key === key)?.color || 'gray'
}

function formatStart(s) {
  if (!s) return ''
  return s.replace('T', ' ')
}

function toLocal(dtStr) {
  // "YYYY-MM-DD HH:MM" -> datetime-local 所需 "YYYY-MM-DDTHH:MM"
  return dtStr ? dtStr.replace(' ', 'T') : ''
}

function fromLocal(localStr) {
  // "YYYY-MM-DDTHH:MM" -> "YYYY-MM-DD HH:MM"
  return localStr ? localStr.replace('T', ' ') : ''
}

async function load() {
  const data = await api.get('/events')
  upcoming.value = data.upcoming
  past.value = data.past
}

function openCreate() {
  editing.value = null
  form.value = { title: '', category: 'game', startLocal: '', note: '' }
  formOpen.value = true
}

function openEdit(e) {
  editing.value = e
  form.value = { title: e.title, category: e.category, startLocal: toLocal(e.start_at), note: e.note }
  formOpen.value = true
}

async function submit() {
  const title = form.value.title.trim()
  if (!title) return
  const payload = {
    title,
    category: form.value.category,
    start_at: fromLocal(form.value.startLocal),
    note: form.value.note.trim(),
  }
  if (editing.value) {
    await api.put(`/events/${editing.value.id}`, payload)
    showToast('已保存', 'success')
  } else {
    await api.post('/events', payload)
    showToast('已创建', 'success')
  }
  formOpen.value = false
  await load()
}

async function toggleDone(e) {
  await api.put(`/events/${e.id}`, { done: !e.done })
  await load()
  showToast(e.done ? '已恢复为待进行' : '已完成', 'success')
}

function askDelete(e) {
  deleting.value = {
    ...e,
    run: async () => {
      await api.del(`/events/${e.id}`)
      await load()
    },
  }
}

async function doDelete() {
  await deleting.value.run()
  deleting.value = null
  showToast('已删除', 'success')
}

onMounted(load)
</script>

<style scoped>
.head {
  margin-bottom: var(--sp-3);
}

.head .page-title {
  margin-bottom: 0;
}

.group {
  margin-bottom: var(--sp-4);
}

.group-title {
  font-size: var(--fs-sm);
  margin-bottom: var(--sp-2);
}

.event-card {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
}

.event-card.past {
  opacity: 0.72;
}

.item-main {
  min-width: 0;
}

.item-title {
  font-weight: 500;
}

.item-time {
  font-size: var(--fs-sm);
  margin-top: 2px;
}

.item-note {
  font-size: var(--fs-sm);
  margin-top: 2px;
}

.done-btn {
  width: 26px;
  height: 26px;
  min-width: 26px;
  border-radius: 50%;
  border: 1.5px solid var(--c-primary);
  color: var(--c-primary);
  background: transparent;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.done-btn:hover {
  background: var(--c-primary);
  color: #fff;
}

.icon-btn {
  font-size: 15px;
  padding: 4px;
  opacity: 0.7;
}

.icon-btn:hover {
  opacity: 1;
}
</style>
