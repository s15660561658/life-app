<template>
  <div class="page">
    <!-- 头部 -->
    <div class="home-head">
      <h2 class="page-title">{{ dateCN }}</h2>
      <div class="today-progress" v-if="stats.tasks_today_total">
        <div class="progress">
          <div class="progress-bar" :style="{ width: progressPct + '%' }"></div>
        </div>
        <span class="muted">今日 {{ stats.tasks_today_done }}/{{ stats.tasks_today_total }}</span>
      </div>
      <div class="muted" v-else>今天还没有安排任务</div>
    </div>

    <!-- 今日计划 + 备忘录 -->
    <div class="two-col">
      <div class="card home-card">
        <div class="row card-head">
          <span class="card-title">📅 今日计划</span>
          <router-link to="/today" class="muted link">全部 ›</router-link>
        </div>
        <div v-for="t in topTasks" :key="t.id" class="task-row">
          <Checkbox :model-value="t.done" @update:model-value="toggleTask(t)" />
          <span class="grow task-text" :class="{ done: t.done }">{{ t.title }}</span>
          <span v-if="t.start_time" class="muted task-time">{{ t.start_time }}</span>
        </div>
        <div v-if="!tasks.length" class="muted empty-hint">暂无任务，去「今日计划」添加</div>
        <div v-else-if="tasks.length > 5" class="muted more-hint">还有 {{ tasks.length - 5 }} 条…</div>
      </div>

      <div class="card home-card">
        <div class="row card-head">
          <span class="card-title">📝 备忘录</span>
          <router-link to="/memos" class="muted link">全部 ›</router-link>
        </div>
        <input v-model="memoText" class="input" placeholder="回车快速记一条…" maxlength="200"
          @keydown.enter.prevent="addMemo" />
        <div v-for="m in topMemos" :key="m.id" class="memo-row">
          <span class="grow memo-text">{{ m.content }}</span>
        </div>
        <div v-if="!memos.length" class="muted empty-hint">暂无备忘</div>
      </div>
    </div>

    <!-- 四张摘要卡 -->
    <div class="sum-grid">
      <router-link to="/dev" class="card sum-card">
        <div class="sum-icon">💻</div>
        <div class="sum-title">开发</div>
        <div class="sum-line">进行中 {{ stats.projects_ongoing ?? 0 }} · Bug {{ stats.bugs_unresolved ?? 0 }}</div>
      </router-link>
      <router-link to="/fitness" class="card sum-card">
        <div class="sum-icon">🏋️</div>
        <div class="sum-title">健身</div>
        <div class="sum-line">{{ stats.workout_today ? '今日已练 ✓' : '今日未练' }} · 累计 {{ stats.workout_total ?? 0 }} 次</div>
      </router-link>
      <router-link to="/diet" class="card sum-card">
        <div class="sum-icon">🍽️</div>
        <div class="sum-title">饮食</div>
        <div class="sum-line">今日 {{ stats.diet_intake_today ?? 0 }} / {{ stats.diet_target ?? 2000 }} 千卡</div>
      </router-link>
      <router-link to="/entertainment" class="card sum-card">
        <div class="sum-icon">🎮</div>
        <div class="sum-title">娱乐</div>
        <div class="sum-line">{{ nextEventLine }}</div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, formatDateCN, todayStr } from '../api'
import Checkbox from '../components/Checkbox.vue'
import { showToast } from '../stores/toast'

const stats = ref({})
const tasks = ref([])
const memos = ref([])
const memoText = ref('')

const dateCN = computed(() => formatDateCN(todayStr()))
const topTasks = computed(() => tasks.value.slice(0, 5))
const topMemos = computed(() => memos.value.slice(0, 5))
const progressPct = computed(() => {
  const t = stats.value.tasks_today_total || 0
  return t ? Math.round(((stats.value.tasks_today_done || 0) / t) * 100) : 0
})

const nextEventLine = computed(() => {
  const e = stats.value.next_event
  return e ? `下一场：${e.title}` : '暂无待进行日程'
})

async function load() {
  const today = todayStr()
  stats.value = await api.get('/stats')
  tasks.value = await api.get(`/tasks?date=${today}`)
  memos.value = await api.get('/memos?limit=5')
}

async function toggleTask(t) {
  await api.put(`/tasks/${t.id}`, { done: !t.done })
  await load()
}

async function addMemo() {
  const content = memoText.value.trim()
  if (!content) return
  await api.post('/memos', { content })
  memoText.value = ''
  showToast('已记录', 'success')
  memos.value = await api.get('/memos?limit=5')
  stats.value = await api.get('/stats')
}

onMounted(load)
</script>

<style scoped>
.home-head {
  margin-bottom: var(--sp-4);
}

.today-progress {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.today-progress .progress {
  flex: 1;
  max-width: 320px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

@media (max-width: 767px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}

.home-card {
  padding: var(--sp-4);
}

.card-head {
  margin-bottom: var(--sp-3);
}

.card-title {
  font-weight: 600;
}

.link {
  font-size: var(--fs-sm);
}

.task-row,
.memo-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 7px 0;
  border-bottom: 1px dashed var(--c-line);
}

.task-row:last-of-type,
.memo-row:last-of-type {
  border-bottom: none;
}

.task-text.done {
  text-decoration: line-through;
  color: var(--c-text-3);
}

.task-time {
  font-size: var(--fs-sm);
}

.memo-text {
  font-size: var(--fs-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-card .input {
  margin-bottom: var(--sp-2);
}

.empty-hint,
.more-hint {
  font-size: var(--fs-sm);
  padding: var(--sp-2) 0 0;
}

.sum-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--sp-3);
}

@media (max-width: 767px) {
  .sum-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.sum-card {
  text-align: center;
  padding: var(--sp-4) var(--sp-2);
  color: var(--c-text);
}

.sum-icon {
  font-size: 26px;
}

.sum-title {
  font-weight: 600;
  margin: var(--sp-1) 0;
}

.sum-line {
  font-size: var(--fs-xs);
  color: var(--c-text-2);
}
</style>
