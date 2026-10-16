<template>
  <div class="page">
    <h2 class="page-title">开发工作</h2>

    <div class="seg">
      <button v-for="t in tabs" :key="t.key" class="seg-item" :class="{ active: tab === t.key }"
        @click="tab = t.key">{{ t.label }}</button>
    </div>

    <!-- ===================== 项目 ===================== -->
    <div v-if="tab === 'projects'">
      <div class="row list-head">
        <span class="muted grow">{{ projects.length }} 个项目</span>
        <button class="btn btn-primary btn-sm" @click="openProjectForm()">＋ 新建项目</button>
      </div>

      <div v-for="p in projects" :key="p.id" class="card project-card">
        <div class="row">
          <div class="grow">
            <div class="proj-name">
              {{ p.name }}
              <Tag :type="statusMeta[p.status].type">{{ statusMeta[p.status].label }}</Tag>
            </div>
            <div class="muted">
              {{ p.tasks.filter(t => t.done).length }}/{{ p.tasks.length }} 任务
              <template v-if="p.deadline"> · 截止 {{ p.deadline }}</template>
            </div>
          </div>
          <button class="icon-btn" @click="openProjectForm(p)">✏️</button>
          <button class="icon-btn" @click="askDeleteProject(p)">🗑️</button>
        </div>
        <div class="progress">
          <div class="progress-bar" :style="{ width: progressOf(p) + '%' }"></div>
        </div>
        <div class="row proj-foot">
          <button class="btn btn-plain btn-sm" @click="toggleExpand(p.id)">
            {{ expanded === p.id ? '收起任务' : `任务清单（${p.tasks.length}）` }}
          </button>
          <select class="select status-select" :value="p.status" @change="changeStatus(p, $event.target.value)">
            <option value="ongoing">进行中</option>
            <option value="done">已完成</option>
            <option value="paused">搁置</option>
          </select>
        </div>

        <div v-if="expanded === p.id" class="ptasks">
          <div v-for="t in p.tasks" :key="t.id" class="row ptask">
            <Checkbox :model-value="t.done" @update:model-value="toggleProjectTask(p, t)" />
            <span class="grow ptask-title" :class="{ done: t.done }">{{ t.title }}</span>
            <button class="icon-btn" @click="askDeleteProjectTask(p, t)">✕</button>
          </div>
          <div class="row ptask-add">
            <input v-model="newTaskTitle[p.id]" class="input" placeholder="添加任务，回车确认"
              maxlength="100" @keydown.enter="addProjectTask(p)" />
          </div>
        </div>
      </div>

      <EmptyState v-if="!projects.length" text="还没有项目，点右上角新建" icon="📁" />
    </div>

    <!-- ===================== Bug ===================== -->
    <div v-if="tab === 'bugs'">
      <div class="row list-head">
        <div class="row grow">
          <select v-model="bugFilter.status" class="select filter-select">
            <option value="">全部状态</option>
            <option value="open">待处理</option>
            <option value="in_progress">处理中</option>
            <option value="resolved">已解决</option>
          </select>
          <select v-model="bugFilter.project_id" class="select filter-select">
            <option value="">全部项目</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <button class="btn btn-primary btn-sm" @click="openBugForm()">＋ 新建 Bug</button>
      </div>

      <div v-for="b in filteredBugs" :key="b.id" class="card bug-card">
        <div class="row">
          <div class="grow bug-main">
            <div class="bug-title">{{ b.title }} <Tag :type="priorityMeta[b.priority].type">{{ priorityMeta[b.priority].label }}</Tag>
              <Tag :type="bugStatusMeta[b.status].type">{{ bugStatusMeta[b.status].label }}</Tag>
            </div>
            <div class="muted">
              {{ b.created_at }}
              <template v-if="projectName(b.project_id)"> · {{ projectName(b.project_id) }}</template>
            </div>
            <div v-if="b.description" class="bug-desc muted">{{ b.description }}</div>
            <div v-if="b.solution" class="bug-solution">✅ {{ b.solution }}</div>
          </div>
        </div>
        <div class="row bug-actions">
          <button v-if="b.status === 'open'" class="btn btn-plain btn-sm" @click="flowBug(b, 'in_progress')">开始处理</button>
          <button v-if="b.status === 'in_progress'" class="btn btn-plain btn-sm" @click="openSolve(b)">填写解决记录</button>
          <button v-if="b.status !== 'resolved'" class="btn btn-plain btn-sm" @click="flowBug(b, 'resolved')">标记已解决</button>
          <span class="grow"></span>
          <button class="icon-btn" @click="openBugForm(b)">✏️</button>
          <button class="icon-btn" @click="askDeleteBug(b)">🗑️</button>
        </div>
      </div>

      <EmptyState v-if="!filteredBugs.length" text="没有符合条件的 Bug" icon="🐞" />
    </div>

    <!-- ===================== 笔记 ===================== -->
    <div v-if="tab === 'notes'">
      <div class="row list-head">
        <input v-model="noteQuery" class="input grow" placeholder="搜索标题与内容…" />
        <select v-model="noteTag" class="select filter-select">
          <option value="">全部标签</option>
          <option v-for="t in allTags" :key="t" :value="t">{{ t }}</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="openNoteForm()">＋ 新建</button>
      </div>

      <div v-for="n in notes" :key="n.id" class="card note-card" @click="openNoteForm(n)">
        <div class="note-title">{{ n.title }}</div>
        <div v-if="n.content" class="muted note-brief">{{ n.content }}</div>
        <div class="row note-foot">
          <Tag v-for="t in n.tags" :key="t" type="purple">{{ t }}</Tag>
          <span class="grow"></span>
          <span class="muted">{{ n.updated_at }}</span>
          <button class="icon-btn" @click.stop="askDeleteNote(n)">🗑️</button>
        </div>
      </div>

      <EmptyState v-if="!notes.length" text="没有符合条件的笔记" icon="📚" />
    </div>

    <!-- ===================== 弹层们 ===================== -->
    <Modal :open="projectForm.open" :title="projectForm.editing ? '编辑项目' : '新建项目'" @close="projectForm.open = false">
      <form @submit.prevent="submitProject">
        <div class="field">
          <label class="field-label">项目名 *</label>
          <input v-model="projectForm.name" class="input" required maxlength="50" />
        </div>
        <div class="field">
          <label class="field-label">状态</label>
          <select v-model="projectForm.status" class="select">
            <option value="ongoing">进行中</option>
            <option value="done">已完成</option>
            <option value="paused">搁置</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">截止日期（可选）</label>
          <input v-model="projectForm.deadline" type="date" class="input" />
        </div>
        <div class="field">
          <label class="field-label">备注</label>
          <textarea v-model="projectForm.note" class="textarea"></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <Modal :open="bugForm.open" :title="bugForm.editing ? '编辑 Bug' : '新建 Bug'" @close="bugForm.open = false">
      <form @submit.prevent="submitBug">
        <div class="field">
          <label class="field-label">标题 *</label>
          <input v-model="bugForm.title" class="input" required maxlength="100" />
        </div>
        <div class="field">
          <label class="field-label">描述</label>
          <textarea v-model="bugForm.description" class="textarea"></textarea>
        </div>
        <div class="row">
          <div class="field grow">
            <label class="field-label">优先级</label>
            <select v-model="bugForm.priority" class="select">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div class="field grow">
            <label class="field-label">所属项目</label>
            <select v-model="bugForm.project_id" class="select">
              <option :value="null">不关联</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
        </div>
        <div class="field" v-if="bugForm.editing">
          <label class="field-label">状态</label>
          <select v-model="bugForm.status" class="select">
            <option value="open">待处理</option>
            <option value="in_progress">处理中</option>
            <option value="resolved">已解决</option>
          </select>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <Modal :open="solveOpen" title="解决记录" @close="solveOpen = false">
      <form @submit.prevent="submitSolution">
        <div class="field">
          <textarea v-model="solutionText" class="textarea" placeholder="怎么解决的？" autofocus></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存并标记已解决</button>
      </form>
    </Modal>

    <Modal :open="noteForm.open" :title="noteForm.editing ? '编辑笔记' : '新建笔记'" @close="noteForm.open = false">
      <form @submit.prevent="submitNote">
        <div class="field">
          <label class="field-label">标题 *</label>
          <input v-model="noteForm.title" class="input" required maxlength="100" />
        </div>
        <div class="field">
          <label class="field-label">内容</label>
          <textarea v-model="noteForm.content" class="textarea" style="min-height: 140px"></textarea>
        </div>
        <div class="field">
          <label class="field-label">标签（逗号分隔）</label>
          <input v-model="noteForm.tagsText" class="input" placeholder="python, 前端" />
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="confirm.open" :title="confirm.title" :message="confirm.message"
      confirm-text="删除" danger @confirm="confirm.onOk" @cancel="confirm.open = false" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import Checkbox from '../components/Checkbox.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import Modal from '../components/Modal.vue'
import Tag from '../components/Tag.vue'
import { showToast } from '../stores/toast'

const tab = ref('projects')
const tabs = [
  { key: 'projects', label: '项目' },
  { key: 'bugs', label: 'Bug 清单' },
  { key: 'notes', label: '笔记' },
]

// ---------- 通用确认 ----------
const confirm = reactive({ open: false, title: '', message: '', onOk: () => {} })
function askConfirm(title, message, onOk) {
  confirm.title = title
  confirm.message = message
  confirm.onOk = async () => {
    confirm.open = false
    await onOk()
  }
  confirm.open = true
}

// ---------- 项目 ----------
const projects = ref([])
const expanded = ref(null)
const newTaskTitle = reactive({})

const statusMeta = {
  ongoing: { label: '进行中', type: 'blue' },
  done: { label: '已完成', type: 'green' },
  paused: { label: '搁置', type: 'gray' },
}

const projectForm = reactive({ open: false, editing: null, name: '', status: 'ongoing', deadline: '', note: '' })

function progressOf(p) {
  if (!p.tasks.length) return 0
  return Math.round((p.tasks.filter((t) => t.done).length / p.tasks.length) * 100)
}

async function loadProjects() {
  projects.value = await api.get('/projects')
}

function openProjectForm(p = null) {
  projectForm.editing = p
  projectForm.name = p?.name || ''
  projectForm.status = p?.status || 'ongoing'
  projectForm.deadline = p?.deadline || ''
  projectForm.note = p?.note || ''
  projectForm.open = true
}

async function submitProject() {
  const body = {
    name: projectForm.name.trim(),
    status: projectForm.status,
    deadline: projectForm.deadline || null,
    note: projectForm.note.trim(),
  }
  if (!body.name) return
  if (projectForm.editing) {
    await api.put(`/projects/${projectForm.editing.id}`, body)
    showToast('已保存', 'success')
  } else {
    await api.post('/projects', body)
    showToast('已创建', 'success')
  }
  projectForm.open = false
  await loadProjects()
}

function toggleExpand(id) {
  expanded.value = expanded.value === id ? null : id
}

async function changeStatus(p, status) {
  await api.put(`/projects/${p.id}`, { status })
  showToast('状态已切换', 'success')
  await loadProjects()
}

async function addProjectTask(p) {
  const title = (newTaskTitle[p.id] || '').trim()
  if (!title) return
  await api.post(`/projects/${p.id}/tasks`, { title })
  newTaskTitle[p.id] = ''
  await loadProjects()
}

async function toggleProjectTask(p, t) {
  await api.put(`/projects/${p.id}/tasks/${t.id}`, { done: !t.done })
  await loadProjects()
}

function askDeleteProjectTask(p, t) {
  askConfirm('删除任务', `确定删除任务「${t.title}」吗？`, async () => {
    await api.del(`/projects/${p.id}/tasks/${t.id}`)
    showToast('已删除', 'success')
    await loadProjects()
  })
}

function askDeleteProject(p) {
  askConfirm('删除项目', `确定删除项目「${p.name}」吗？\n其任务一并删除；关联的 Bug 将被保留但解除关联。`, async () => {
    await api.del(`/projects/${p.id}`)
    showToast('已删除', 'success')
    await loadProjects()
    await loadBugs()
  })
}

// ---------- Bug ----------
const bugs = ref([])
const bugFilter = reactive({ status: '', project_id: '' })

const priorityMeta = {
  high: { label: '高', type: 'red' },
  medium: { label: '中', type: 'orange' },
  low: { label: '低', type: 'gray' },
}
const bugStatusMeta = {
  open: { label: '待处理', type: 'red' },
  in_progress: { label: '处理中', type: 'orange' },
  resolved: { label: '已解决', type: 'green' },
}

const bugForm = reactive({ open: false, editing: null, title: '', description: '', priority: 'medium', project_id: null, status: 'open' })
const solveOpen = ref(false)
const solvingBug = ref(null)
const solutionText = ref('')

const filteredBugs = computed(() =>
  bugs.value.filter((b) =>
    (!bugFilter.status || b.status === bugFilter.status) &&
    (bugFilter.project_id === '' || b.project_id === bugFilter.project_id)))

function projectName(pid) {
  const p = projects.value.find((x) => x.id === pid)
  return p?.name
}

async function loadBugs() {
  bugs.value = await api.get('/bugs')
}

function openBugForm(b = null) {
  bugForm.editing = b
  bugForm.title = b?.title || ''
  bugForm.description = b?.description || ''
  bugForm.priority = b?.priority || 'medium'
  bugForm.project_id = b?.project_id ?? null
  bugForm.status = b?.status || 'open'
  bugForm.open = true
}

async function submitBug() {
  const base = {
    title: bugForm.title.trim(),
    description: bugForm.description.trim(),
    priority: bugForm.priority,
    project_id: bugForm.project_id,
  }
  if (!base.title) return
  if (bugForm.editing) {
    await api.put(`/bugs/${bugForm.editing.id}`, { ...base, status: bugForm.status })
    showToast('已保存', 'success')
  } else {
    await api.post('/bugs', base)
    showToast('已创建', 'success')
  }
  bugForm.open = false
  await loadBugs()
}

async function flowBug(b, status) {
  if (status === 'resolved' && !b.solution) {
    openSolve(b)
    return
  }
  await api.put(`/bugs/${b.id}`, { status })
  showToast(status === 'resolved' ? '已解决 🎉' : '开始处理', 'success')
  await loadBugs()
}

function openSolve(b) {
  solvingBug.value = b
  solutionText.value = b.solution || ''
  solveOpen.value = true
}

async function submitSolution() {
  await api.put(`/bugs/${solvingBug.value.id}`, { solution: solutionText.value.trim(), status: 'resolved' })
  solveOpen.value = false
  showToast('已解决 🎉', 'success')
  await loadBugs()
}

function askDeleteBug(b) {
  askConfirm('删除 Bug', `确定删除「${b.title}」吗？`, async () => {
    await api.del(`/bugs/${b.id}`)
    showToast('已删除', 'success')
    await loadBugs()
  })
}

// ---------- 笔记 ----------
const notes = ref([])
const noteQuery = ref('')
const noteTag = ref('')
const noteForm = reactive({ open: false, editing: null, title: '', content: '', tagsText: '' })

const allTags = computed(() => {
  const s = new Set()
  notes.value.forEach((n) => n.tags.forEach((t) => s.add(t)))
  return [...s]
})

async function loadNotes() {
  const params = new URLSearchParams()
  if (noteQuery.value.trim()) params.set('q', noteQuery.value.trim())
  if (noteTag.value) params.set('tag', noteTag.value)
  const qs = params.toString()
  notes.value = await api.get(`/notes${qs ? '?' + qs : ''}`)
}

watch([noteQuery, noteTag], loadNotes)

function openNoteForm(n = null) {
  noteForm.editing = n
  noteForm.title = n?.title || ''
  noteForm.content = n?.content || ''
  noteForm.tagsText = n?.tags.join(', ') || ''
  noteForm.open = true
}

async function submitNote() {
  const title = noteForm.title.trim()
  if (!title) return
  const body = {
    title,
    content: noteForm.content.trim(),
    tags: noteForm.tagsText.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
  }
  if (noteForm.editing) {
    await api.put(`/notes/${noteForm.editing.id}`, body)
    showToast('已保存', 'success')
  } else {
    await api.post('/notes', body)
    showToast('已创建', 'success')
  }
  noteForm.open = false
  await loadNotes()
}

function askDeleteNote(n) {
  askConfirm('删除笔记', `确定删除「${n.title}」吗？`, async () => {
    await api.del(`/notes/${n.id}`)
    showToast('已删除', 'success')
    await loadNotes()
  })
}

// ---------- 初始化 ----------
onMounted(async () => {
  await Promise.all([loadProjects(), loadBugs(), loadNotes()])
})
</script>

<style scoped>
.seg {
  display: flex;
  background: var(--c-line);
  border-radius: var(--r-md);
  padding: 3px;
  margin-bottom: var(--sp-4);
}

.seg-item {
  flex: 1;
  padding: 8px 0;
  border-radius: var(--r-sm);
  font-size: var(--fs-sm);
  color: var(--c-text-2);
}

.seg-item.active {
  background: var(--c-card);
  color: var(--c-text);
  font-weight: 500;
  box-shadow: var(--shadow-card);
}

.list-head {
  margin-bottom: var(--sp-3);
}

.filter-select {
  width: auto;
  min-width: 104px;
}

/* 项目卡 */
.project-card {
  margin-bottom: var(--sp-3);
}

.proj-name {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.progress {
  height: 6px;
  background: var(--c-line);
  border-radius: var(--r-full);
  overflow: hidden;
  margin: var(--sp-3) 0;
}

.progress-bar {
  height: 100%;
  background: var(--c-primary);
  border-radius: var(--r-full);
  transition: width 0.2s;
}

.proj-foot {
  justify-content: space-between;
}

.status-select {
  width: auto;
  padding: 5px 8px;
  font-size: var(--fs-sm);
}

.ptasks {
  border-top: 1px solid var(--c-line);
  padding-top: var(--sp-3);
}

.ptask {
  padding: 6px 0;
}

.ptask-title.done {
  text-decoration: line-through;
  color: var(--c-text-3);
}

.ptask-add {
  margin-top: var(--sp-2);
}

.icon-btn {
  font-size: 15px;
  padding: 4px;
  opacity: 0.7;
}

.icon-btn:hover {
  opacity: 1;
}

/* Bug 卡 */
.bug-card {
  margin-bottom: var(--sp-3);
}

.bug-title {
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.bug-desc {
  margin-top: 4px;
  white-space: pre-wrap;
}

.bug-solution {
  margin-top: 6px;
  background: var(--c-success-weak);
  color: var(--c-success);
  border-radius: var(--r-sm);
  padding: 6px 10px;
  font-size: var(--fs-sm);
  white-space: pre-wrap;
}

.bug-actions {
  margin-top: var(--sp-3);
}

/* 笔记卡 */
.note-card {
  margin-bottom: var(--sp-3);
  cursor: pointer;
}

.note-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.note-brief {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: var(--sp-2);
  white-space: pre-wrap;
}

.note-foot {
  flex-wrap: wrap;
}
</style>
