<template>
  <div class="page">
    <!-- 移动端健康分段切换 -->
    <div class="health-seg">
      <router-link to="/fitness" class="hs-item active">健身</router-link>
      <router-link to="/diet" class="hs-item">饮食</router-link>
    </div>

    <div class="row head">
      <h2 class="page-title grow">健身计划</h2>
      <button class="btn btn-primary" @click="startTraining">▶ 开始训练</button>
    </div>

    <div class="subtabs">
      <button class="st-item" :class="{ active: sub === 'plan' }" @click="sub = 'plan'">计划表</button>
      <button class="st-item" :class="{ active: sub === 'logs' }" @click="sub = 'logs'">训练打卡</button>
      <button class="st-item" :class="{ active: sub === 'body' }" @click="sub = 'body'">身体数据</button>
    </div>

    <!-- ================ 计划表 ================ -->
    <div v-if="sub === 'plan'">
      <div class="row list-head">
        <span class="muted grow">点某天卡片编辑动作；可复制整周模板</span>
        <button class="btn btn-plain btn-sm" @click="copyOpen = true">⧉ 复制某天到另一天</button>
      </div>

      <div class="plan-grid">
        <div v-for="d in 7" :key="d" class="card day-card" :class="{ today: d === todayDow() }">
          <div class="row day-head">
            <span class="day-name">{{ dayNames[d - 1] }}</span>
            <span class="muted">{{ plan[String(d)].length ? `${plan[String(d)].length} 个动作` : '休息' }}</span>
            <button class="icon-btn" @click="openDayEditor(d)">✏️</button>
          </div>
          <div v-for="(e, i) in plan[String(d)]" :key="i" class="exercise-row">
            <span class="ex-name">{{ e.name }}</span>
            <span class="muted">{{ e.sets }}组 × {{ e.reps }}次 · 休{{ e.rest_seconds }}s</span>
          </div>
          <div v-if="!plan[String(d)].length" class="muted rest-hint">休息日</div>
        </div>
      </div>
    </div>

    <!-- ================ 训练打卡 ================ -->
    <div v-if="sub === 'logs'">
      <div class="card summary-card">
        <div class="summary-row">
          <div class="summary-item">
            <div class="summary-num">{{ summary.total }}</div>
            <div class="muted">累计次数</div>
          </div>
          <div class="summary-item">
            <div class="summary-num">{{ summary.week_count }}</div>
            <div class="muted">本周次数</div>
          </div>
          <div class="summary-item">
            <div class="summary-num">{{ summary.streak_days }}</div>
            <div class="muted">连续天数</div>
          </div>
        </div>
        <div class="row" style="margin-top: 12px">
          <button class="btn btn-primary grow" @click="startTraining">▶ 开始今天训练</button>
          <button class="btn btn-plain" @click="openManualLog">手动补录</button>
        </div>
      </div>

      <div v-for="l in logs" :key="l.id" class="card log-card">
        <div class="row">
          <div class="grow">
            <div class="log-date">{{ l.date }} <span class="muted">· {{ Math.round(l.duration_seconds / 60) }} 分钟</span></div>
            <div class="muted log-ex">{{ l.exercises.map(e => `${e.name} ${e.sets}×${e.reps}`).join('，') || '自由训练' }}</div>
          </div>
          <button class="icon-btn" @click="askDeleteLog(l)">🗑️</button>
        </div>
      </div>

      <EmptyState v-if="!logs.length" text="还没有训练记录" icon="🏋️" />
    </div>

    <!-- ================ 身体数据 ================ -->
    <div v-if="sub === 'body'">
      <div class="row list-head">
        <span class="muted grow">按日期倒序</span>
        <button class="btn btn-primary btn-sm" @click="openBodyForm">＋ 记体重</button>
      </div>

      <div v-for="b in bodyList" :key="b.id" class="card body-card">
        <div class="row">
          <div class="grow">
            <span class="body-weight">{{ b.weight_kg }}</span> kg
            <span class="muted"> · {{ b.date }}</span>
          </div>
          <button class="icon-btn" @click="askDeleteBody(b)">🗑️</button>
        </div>
      </div>

      <EmptyState v-if="!bodyList.length" text="还没有身体数据记录" icon="⚖️" />
    </div>

    <!-- ===================== 弹层 ===================== -->
    <Modal :open="dayEditor.open" :title="`${dayNames[dayEditor.day - 1]} · 编辑动作`" @close="dayEditor.open = false">
      <div v-for="(e, i) in dayEditor.exercises" :key="i" class="row ex-edit">
        <input v-model="e.name" class="input grow" placeholder="动作名" maxlength="30" />
        <input v-model.number="e.sets" type="number" min="1" class="input num" placeholder="组" />
        <input v-model.number="e.reps" type="number" min="1" class="input num" placeholder="次" />
        <input v-model.number="e.rest_seconds" type="number" min="0" class="input num" placeholder="秒" />
        <button class="icon-btn" @click="dayEditor.exercises.splice(i, 1)">✕</button>
      </div>
      <button class="btn btn-plain btn-block" @click="addExercise">＋ 添加动作</button>
      <button class="btn btn-primary btn-block" style="margin-top: 12px" @click="saveDay">保存</button>
    </Modal>

    <Modal :open="copyOpen" title="复制某天计划到另一天" @close="copyOpen = false">
      <div class="field">
        <label class="field-label">从</label>
        <select v-model="copyFrom" class="select">
          <option v-for="d in 7" :key="d" :value="d">{{ dayNames[d - 1] }}（{{ plan[String(d)].length }} 个动作）</option>
        </select>
      </div>
      <div class="field">
        <label class="field-label">到</label>
        <select v-model="copyTo" class="select">
          <option v-for="d in 7" :key="d" :value="d">{{ dayNames[d - 1] }}</option>
        </select>
      </div>
      <button class="btn btn-primary btn-block" @click="doCopy">复制</button>
    </Modal>

    <Modal :open="manualLogOpen" title="手动补录训练" @close="manualLogOpen = false">
      <form @submit.prevent="submitManualLog">
        <div class="field">
          <label class="field-label">日期</label>
          <input v-model="manualLog.date" type="date" class="input" required />
        </div>
        <div class="field">
          <label class="field-label">时长（分钟）</label>
          <input v-model.number="manualLog.minutes" type="number" min="1" class="input" required />
        </div>
        <div class="field">
          <label class="field-label">动作明细（可选）</label>
          <div v-for="(e, i) in manualLog.exercises" :key="i" class="row ex-edit">
            <input v-model="e.name" class="input grow" placeholder="动作名" maxlength="30" />
            <input v-model.number="e.sets" type="number" min="1" class="input num" placeholder="组" />
            <input v-model.number="e.reps" type="number" min="1" class="input num" placeholder="次" />
            <button class="icon-btn" @click="manualLog.exercises.splice(i, 1)">✕</button>
          </div>
          <button class="btn btn-plain btn-sm" @click="manualLog.exercises.push({ name: '', sets: 3, reps: 10 })">＋ 添加动作</button>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <Modal :open="bodyFormOpen" title="记录体重" @close="bodyFormOpen = false">
      <form @submit.prevent="submitBody">
        <div class="field">
          <label class="field-label">日期</label>
          <input v-model="bodyForm.date" type="date" class="input" required />
        </div>
        <div class="field">
          <label class="field-label">体重（kg）*</label>
          <input v-model.number="bodyForm.weight_kg" type="number" step="0.1" min="1" class="input" required />
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="!!deleting" title="确认删除" :message="deleting?.msg || '确定删除吗？'"
      confirm-text="删除" danger @confirm="doDelete" @cancel="deleting = null" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, todayStr } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import Modal from '../components/Modal.vue'
import { showToast } from '../stores/toast'

const router = useRouter()
const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

function todayDow() {
  const d = new Date().getDay()
  return d === 0 ? 7 : d
}

const sub = ref('plan')
const plan = ref({ 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] })
const logs = ref([])
const summary = ref({ total: 0, week_count: 0, streak_days: 0 })
const bodyList = ref([])

// 计划表编辑
const dayEditor = reactive({ open: false, day: 1, exercises: [] })
const copyOpen = ref(false)
const copyFrom = ref(1)
const copyTo = ref(2)

// 打卡
const manualLogOpen = ref(false)
const manualLog = reactive({ date: todayStr(), minutes: 30, exercises: [] })
const deleting = ref(null)

// 身体数据
const bodyFormOpen = ref(false)
const bodyForm = reactive({ date: todayStr(), weight_kg: null })

async function loadPlan() {
  plan.value = await api.get('/workout/plan')
}

async function loadLogs() {
  logs.value = await api.get('/workout/logs')
  summary.value = await api.get('/workout/summary')
}

async function loadBody() {
  bodyList.value = await api.get('/body')
}

onMounted(() => {
  loadPlan()
  loadLogs()
  loadBody()
})

function startTraining() {
  router.push('/training')
}

// ---- 计划表 ----
function openDayEditor(d) {
  dayEditor.day = d
  dayEditor.exercises = plan.value[String(d)].map((e) => ({ ...e }))
  dayEditor.open = true
}

function addExercise() {
  const rest = planDefaultRest()
  dayEditor.exercises.push({ name: '', sets: 3, reps: 10, rest_seconds: rest })
}

function planDefaultRest() {
  const today = plan.value[String(todayDow())]
  return today.length ? today[0].rest_seconds : 60
}

async function saveDay() {
  const exercises = dayEditor.exercises.filter((e) => e.name.trim())
  if (exercises.some((e) => e.sets < 1 || e.reps < 1 || e.rest_seconds < 0)) {
    showToast('组数/次数须 ≥ 1，间歇 ≥ 0', 'error')
    return
  }
  await api.put(`/workout/plan/${dayEditor.day}`, {
    exercises: exercises.map((e) => ({ ...e, name: e.name.trim() })),
  })
  dayEditor.open = false
  showToast('计划已保存', 'success')
  await loadPlan()
}

async function doCopy() {
  if (copyFrom.value === copyTo.value) {
    showToast('请选择不同的两天', 'error')
    return
  }
  await api.put(`/workout/plan/${copyTo.value}`, { exercises: plan.value[String(copyFrom.value)] })
  copyOpen.value = false
  showToast(`已复制到${dayNames[copyTo.value - 1]}`, 'success')
  await loadPlan()
}

// ---- 打卡 ----
function openManualLog() {
  manualLog.date = todayStr()
  manualLog.minutes = 30
  manualLog.exercises = []
  manualLogOpen.value = true
}

async function submitManualLog() {
  const exercises = manualLog.exercises
    .filter((e) => e.name.trim())
    .map((e) => ({ name: e.name.trim(), sets: e.sets || 1, reps: e.reps || 1 }))
  await api.post('/workout/logs', {
    date: manualLog.date,
    duration_seconds: Math.round(manualLog.minutes * 60),
    exercises,
  })
  manualLogOpen.value = false
  showToast('已补录', 'success')
  await loadLogs()
}

function askDeleteLog(l) {
  deleting.value = {
    msg: `确定删除 ${l.date} 的训练记录吗？`,
    run: async () => {
      await api.del(`/workout/logs/${l.id}`)
      await loadLogs()
    },
  }
}

// ---- 身体数据 ----
function openBodyForm() {
  bodyForm.date = todayStr()
  bodyForm.weight_kg = null
  bodyFormOpen.value = true
}

async function submitBody() {
  if (!bodyForm.weight_kg || bodyForm.weight_kg <= 0) {
    showToast('请输入有效体重', 'error')
    return
  }
  await api.post('/body', { date: bodyForm.date, weight_kg: bodyForm.weight_kg })
  bodyFormOpen.value = false
  showToast('已记录', 'success')
  await loadBody()
}

function askDeleteBody(b) {
  deleting.value = {
    msg: `确定删除 ${b.date} 的体重记录吗？`,
    run: async () => {
      await api.del(`/body/${b.id}`)
      await loadBody()
    },
  }
}

async function doDelete() {
  await deleting.value.run()
  deleting.value = null
  showToast('已删除', 'success')
}
</script>

<style scoped>
.health-seg {
  display: none;
}

@media (max-width: 767px) {
  .health-seg {
    display: flex;
    background: var(--c-line);
    border-radius: var(--r-md);
    padding: 3px;
    margin-bottom: var(--sp-4);
  }

  .hs-item {
    flex: 1;
    text-align: center;
    padding: 8px 0;
    border-radius: var(--r-sm);
    font-size: var(--fs-sm);
    color: var(--c-text-2);
  }

  .hs-item.active {
    background: var(--c-card);
    color: var(--c-text);
    font-weight: 500;
    box-shadow: var(--shadow-card);
  }
}

.head {
  margin-bottom: var(--sp-3);
}

.head .page-title {
  margin-bottom: 0;
}

.subtabs {
  display: flex;
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}

.st-item {
  padding: 7px 14px;
  border-radius: var(--r-full);
  background: var(--c-line);
  color: var(--c-text-2);
  font-size: var(--fs-sm);
}

.st-item.active {
  background: var(--c-primary);
  color: #fff;
}

.list-head {
  margin-bottom: var(--sp-3);
}

/* 计划表 */
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: var(--sp-3);
}

.day-card.today {
  border: 1.5px solid var(--c-primary);
}

.day-head {
  margin-bottom: var(--sp-2);
}

.day-name {
  font-weight: 600;
}

.exercise-row {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-2);
  padding: 4px 0;
  font-size: var(--fs-sm);
}

.ex-name {
  font-weight: 500;
}

.rest-hint {
  font-size: var(--fs-sm);
  text-align: center;
  padding: 8px 0;
}

.icon-btn {
  font-size: 15px;
  padding: 4px;
  opacity: 0.7;
}

.icon-btn:hover {
  opacity: 1;
}

/* 弹层内动作编辑 */
.ex-edit {
  margin-bottom: var(--sp-2);
}

.num {
  width: 64px;
  text-align: center;
}

/* 打卡 */
.summary-card {
  margin-bottom: var(--sp-4);
}

.summary-row {
  display: flex;
  text-align: center;
}

.summary-item {
  flex: 1;
}

.summary-num {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--c-primary);
}

.log-card,
.body-card {
  margin-bottom: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
}

.log-date {
  font-weight: 500;
}

.log-ex {
  margin-top: 2px;
}

.body-weight {
  font-size: var(--fs-xl);
  font-weight: 700;
}
</style>
