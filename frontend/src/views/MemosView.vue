<template>
  <div class="page">
    <h2 class="page-title">备忘录</h2>

    <div class="card compose">
      <input v-model="draft" class="input compose-input" placeholder="记点什么，回车即存…"
        maxlength="500" @keydown.enter="create" />
    </div>

    <div v-for="m in items" :key="m.id" class="memo card">
      <div class="grow memo-main">
        <div class="memo-content">{{ m.content }}</div>
        <div class="muted">{{ m.created_at }}</div>
      </div>
      <button class="icon-btn" title="编辑" @click="openEdit(m)">✏️</button>
      <button class="icon-btn" title="复制" @click="copyMemo(m)">📋</button>
      <button class="icon-btn" title="删除" @click="askDelete(m)">🗑️</button>
    </div>

    <EmptyState v-if="!items.length" text="还没有备忘录，输入后回车即可保存" icon="📝" />

    <Modal :open="editing !== null" title="编辑备忘录" @close="editing = null">
      <form @submit.prevent="saveEdit">
        <div class="field">
          <textarea v-model="editText" class="textarea" maxlength="500" autofocus></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="deleting !== null" title="删除备忘录" message="确定删除这条备忘录吗？"
      confirm-text="删除" danger @confirm="doDelete" @cancel="deleting = null" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import Modal from '../components/Modal.vue'
import { showToast } from '../stores/toast'

const items = ref([])
const draft = ref('')
const editing = ref(null)
const editText = ref('')
const deleting = ref(null)

async function load() {
  items.value = await api.get('/memos')
}

onMounted(load)

async function create() {
  const content = draft.value.trim()
  if (!content) return
  await api.post('/memos', { content })
  draft.value = ''
  showToast('已保存', 'success')
  await load()
}

function openEdit(m) {
  editing.value = m
  editText.value = m.content
}

async function saveEdit() {
  const content = editText.value.trim()
  if (!content) return
  await api.put(`/memos/${editing.value.id}`, { content })
  editing.value = null
  showToast('已保存', 'success')
  await load()
}

async function copyMemo(m) {
  await api.post('/memos', { content: m.content })
  showToast('已复制一条', 'success')
  await load()
}

function askDelete(m) {
  deleting.value = m
}

async function doDelete() {
  await api.del(`/memos/${deleting.value.id}`)
  deleting.value = null
  showToast('已删除', 'success')
  await load()
}
</script>

<style scoped>
.compose {
  margin-bottom: var(--sp-4);
}

.memo {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
  margin-bottom: var(--sp-2);
}

.memo-content {
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 4px;
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
