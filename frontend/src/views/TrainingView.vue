<template>
  <div class="training">
    <!-- ============ 未开始 ============ -->
    <div v-if="phase === 'idle'" class="tr-center">
      <h1 class="tr-title">训练模式</h1>
      <p class="muted">{{ dayLabel }} · {{ exercises.length ? `${exercises.length} 个动作` : '今天没有安排动作' }}</p>

      <div v-if="exercises.length" class="plan-preview">
        <div v-for="(e, i) in exercises" :key="i" class="row pp-row">
          <span class="grow">{{ e.name }}</span>
          <span class="muted">{{ e.sets }}组 × {{ e.reps }}次 · 休{{ e.rest_seconds }}s</span>
        </div>
      </div>

      <div class="tr-actions">
        <button v-if="exercises.length" class="btn btn-primary btn-lg" @click="start">开始训练</button>
        <button class="btn btn-plain" @click="leave">返回</button>
      </div>
    </div>

    <!-- ============ 训练中 / 休息中 ============ -->
    <div v-else-if="phase === 'working' || phase === 'resting'" class="tr-main">
      <div class="tr-top">
        <button class="btn btn-plain btn-sm" @click="askQuit">✕ 退出</button>
        <span class="muted">{{ totalDoneSets }} / {{ totalSets }} 组 · 已用 {{ elapsedText }}</span>
      </div>

      <div class="tr-progress">
        <div class="tr-progress-bar" :style="{ width: progressPct + '%' }"></div>
      </div>

      <div class="tr-body">
        <template v-if="phase === 'working'">
          <div class="tr-step muted">动作 {{ curExIndex + 1 }}/{{ exercises.length }} · 第 {{ curSet }}/{{ curExercise.sets }} 组</div>
          <h1 class="tr-exname">{{ curExercise.name }}</h1>
          <p class="tr-next muted" v-if="curSet < curExercise.sets">完成后休息 {{ restOf(curExercise) }}s</p>
          <p class="tr-next muted" v-else-if="curExIndex < exercises.length - 1">下一动作：{{ exercises[curExIndex + 1].name }}</p>

          <button class="btn-done" @click="completeSet">完成本组 ✓</button>
        </template>

        <template v-else>
          <div class="tr-step muted">组间休息</div>
          <div class="tr-timer">{{ restText }}</div>
          <p class="tr-next muted">下一个：{{ nextLabel }}</p>
          <div class="tr-rest-actions">
            <button class="btn btn-plain" @click="restPaused = false" v-if="restPaused">继续</button>
            <button class="btn btn-plain" @click="restPaused = true" v-else>暂停</button>
            <button class="btn btn-plain" @click="restRemaining += 15">+15s</button>
            <button class="btn btn-primary" @click="finishRest">跳过休息 »</button>
          </div>
        </template>
      </div>
    </div>

    <!-- ============ 已完成 ============ -->
    <div v-else class="tr-center">
      <div class="done-emoji">🎉</div>
      <h1 class="tr-title">训练完成！</h1>
      <p class="muted">共 {{ totalDoneSets }} 组 · 用时 {{ elapsedText }}</p>
      <div class="tr-actions">
        <button class="btn btn-primary btn-lg" @click="saveLog">生成打卡记录</button>
        <button class="btn btn-plain" @click="quitNoSave">不保存退出</button>
      </div>
    </div>

    <!-- 退出确认 -->
    <ConfirmDialog :open="quitOpen" title="退出训练" message="确定退出本次训练吗？可以选择保存已完成的组数。"
      @confirm="savePartial" @cancel="quitOpen = false">
    </ConfirmDialog>
    <div v-if="quitOpen" class="tr-quit-extra">
      <button class="btn btn-danger" @click="quitNoSave">不保存直接退出</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, pad, todayStr } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { useSettingsStore } from '../stores/settings'
import { showToast } from '../stores/toast'

const router = useRouter()
const settings = useSettingsStore()

const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const phase = ref('idle') // idle | working | resting | finished
const exercises = ref([])
const curExIndex = ref(0)
const curSet = ref(1)
const doneSets = ref([]) // 每动作完成组数，与 exercises 对齐
const startTime = ref(0)
const elapsed = ref(0)
const elapsedTimer = ref(null)

// 组休
const restRemaining = ref(0)
const restTotal = ref(0)
const restPaused = ref(false)
const restTimer = ref(null)

const quitOpen = ref(false)
let audioCtx = null

const curExercise = computed(() => exercises.value[curExIndex.value] || { name: '', sets: 1 })
const totalSets = computed(() => exercises.value.reduce((s, e) => s + e.sets, 0))
const totalDoneSets = computed(() => doneSets.value.reduce((s, n) => s + n, 0))
const progressPct = computed(() => (totalSets.value ? Math.round((totalDoneSets.value / totalSets.value) * 100) : 0))
const elapsedText = computed(() => {
  const s = Math.floor(elapsed.value)
  return `${Math.floor(s / 60)}:${pad(s % 60)}`
})
const restText = computed(() => `${Math.ceil(restRemaining.value)}`)
const nextLabel = computed(() => {
  if (curSet.value < curExercise.value.sets) return `${curExercise.value.name} 第 ${curSet.value + 1} 组`
  const next = exercises.value[curExIndex.value + 1]
  return next ? `${next.name} 第 1 组` : '结束'
})
const dayLabel = computed(() => {
  const d = new Date().getDay()
  return `今天${dayNames[d === 0 ? 6 : d - 1]}`
})

function restOf(e) {
  return e.rest_seconds || settings.default_rest_seconds || 60
}

onMounted(async () => {
  if (!settings.loaded) {
    try { await settings.fetch() } catch { /* 后端不可用时用默认值 */ }
  }
  const plan = await api.get('/workout/plan')
  const dow = new Date().getDay()
  exercises.value = plan[String(dow === 0 ? 7 : dow)] || []
  doneSets.value = exercises.value.map(() => 0)
})

onBeforeUnmount(() => {
  clearInterval(elapsedTimer.value)
  clearInterval(restTimer.value)
})

// ---------- 音频与震动 ----------
function beep() {
  try {
    audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.frequency.value = 880
    gain.gain.setValueAtTime(0.4, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.8)
    osc.start()
    osc.stop(audioCtx.currentTime + 0.8)
  } catch { /* 音频不可用忽略 */ }
  navigator.vibrate?.([300, 150, 300])
}

// ---------- 计时 ----------
function start() {
  startTime.value = Date.now()
  elapsedTimer.value = setInterval(() => {
    elapsed.value = (Date.now() - startTime.value) / 1000
  }, 500)
  phase.value = 'working'
}

function completeSet() {
  doneSets.value[curExIndex.value] += 1
  const moreInExercise = curSet.value < curExercise.value.sets
  if (moreInExercise || curExIndex.value < exercises.value.length - 1) {
    // 进入组休
    restTotal.value = restOf(curExercise.value)
    restRemaining.value = restTotal.value
    restPaused.value = false
    phase.value = 'resting'
    clearInterval(restTimer.value)
    restTimer.value = setInterval(tickRest, 1000)
  } else {
    finish()
  }
}

function tickRest() {
  if (restPaused.value) return
  restRemaining.value -= 1
  if (restRemaining.value <= 0) {
    beep()
    finishRest()
  }
}

function finishRest() {
  clearInterval(restTimer.value)
  const ex = curExercise.value
  if (curSet.value < ex.sets) {
    curSet.value += 1
  } else {
    curExIndex.value += 1
    curSet.value = 1
  }
  phase.value = 'working'
}

function finish() {
  clearInterval(restTimer.value)
  phase.value = 'finished'
}

// ---------- 保存 ----------
function buildPayload() {
  const secs = Math.max(1, Math.round((Date.now() - startTime.value) / 1000))
  const exercisesDone = exercises.value
    .map((e, i) => ({ name: e.name, sets: doneSets.value[i], reps: e.reps }))
    .filter((e) => e.sets > 0)
    .map((e) => ({ ...e, sets: e.sets || 1 }))
  return { date: todayStr(), duration_seconds: secs, exercises: exercisesDone }
}

async function saveLog() {
  await api.post('/workout/logs', buildPayload())
  showToast('已生成打卡记录 💪', 'success')
  cleanup()
  router.push('/fitness')
}

async function savePartial() {
  if (totalDoneSets.value === 0) {
    quitNoSave()
    return
  }
  await api.post('/workout/logs', buildPayload())
  showToast('已保存已完成部分', 'success')
  cleanup()
  router.push('/fitness')
}

function askQuit() {
  quitOpen.value = true
}

function quitNoSave() {
  cleanup()
  router.push('/fitness')
}

function cleanup() {
  quitOpen.value = false
  clearInterval(elapsedTimer.value)
  clearInterval(restTimer.value)
}
</script>

<style scoped>
.training {
  min-height: 100vh;
  background: var(--c-bg);
  display: flex;
  flex-direction: column;
}

.tr-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--sp-6);
  text-align: center;
}

.tr-title {
  font-size: var(--fs-2xl);
  margin-bottom: var(--sp-2);
}

.done-emoji {
  font-size: 64px;
  margin-bottom: var(--sp-3);
}

.plan-preview {
  width: 100%;
  max-width: 420px;
  background: var(--c-card);
  border-radius: var(--r-lg);
  padding: var(--sp-4);
  margin: var(--sp-4) 0;
  text-align: left;
}

.pp-row {
  padding: 6px 0;
  border-bottom: 1px solid var(--c-line);
}

.pp-row:last-child {
  border-bottom: none;
}

.tr-actions {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-4);
}

.btn-lg {
  padding: 14px 34px;
  font-size: var(--fs-lg);
}

/* 训练中 */
.tr-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--sp-4);
  max-width: 640px;
  width: 100%;
  margin: 0 auto;
}

.tr-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-3);
}

.tr-progress {
  height: 8px;
  background: var(--c-line);
  border-radius: var(--r-full);
  overflow: hidden;
}

.tr-progress-bar {
  height: 100%;
  background: var(--c-primary);
  border-radius: var(--r-full);
  transition: width 0.25s ease;
}

.tr-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--sp-4);
  padding: var(--sp-6) 0;
}

.tr-step {
  letter-spacing: 1px;
}

.tr-exname {
  font-size: 42px;
  font-weight: 700;
}

.tr-next {
  min-height: 20px;
}

.tr-timer {
  font-size: 96px;
  font-weight: 700;
  color: var(--c-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.btn-done {
  background: var(--c-success);
  color: #fff;
  font-size: var(--fs-xl);
  font-weight: 600;
  padding: 20px 64px;
  border-radius: var(--r-full);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.35);
}

.btn-done:active {
  transform: scale(0.97);
}

.tr-rest-actions {
  display: flex;
  gap: var(--sp-3);
}

.tr-quit-extra {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 96px;
  display: flex;
  justify-content: center;
  z-index: 121;
}
</style>
