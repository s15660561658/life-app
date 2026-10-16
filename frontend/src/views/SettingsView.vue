<template>
  <div class="page">
    <h2 class="page-title">数据与设置</h2>

    <!-- ============ 统计 ============ -->
    <div class="stats-grid">
      <div class="card stat-card">
        <div class="stat-num">{{ stats.tasks_today_done }}/{{ stats.tasks_today_total }}</div>
        <div class="muted">今日任务完成</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.memos_count }}</div>
        <div class="muted">备忘录条数</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.projects_ongoing }}</div>
        <div class="muted">进行中项目</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.bugs_unresolved }}</div>
        <div class="muted">未解决 Bug</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.workout_total }}</div>
        <div class="muted">累计训练次数</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.diet_intake_today }}</div>
        <div class="muted">今日摄入千卡</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ stats.diet_days }}</div>
        <div class="muted">饮食记录天数</div>
      </div>
      <div class="card stat-card">
        <div class="stat-num">{{ nextEventText }}</div>
        <div class="muted">下一个日程</div>
      </div>
    </div>

    <!-- ============ 偏好设置 ============ -->
    <div class="card section">
      <div class="section-title">偏好设置</div>
      <form @submit.prevent="saveSettings">
        <div class="row">
          <div class="field grow">
            <label class="field-label">每日热量目标（千卡）</label>
            <input v-model.number="form.calorie_target" type="number" min="1" class="input" required />
          </div>
          <div class="field grow">
            <label class="field-label">默认组间休息（秒）</label>
            <input v-model.number="form.default_rest_seconds" type="number" min="0" class="input" required />
          </div>
        </div>
        <button class="btn btn-primary" type="submit">保存设置</button>
      </form>
    </div>

    <!-- ============ 备份与恢复 ============ -->
    <div class="card section">
      <div class="section-title">备份与恢复</div>
      <p class="muted sec-hint">导出为单个 JSON 文件，包含全部模块数据；恢复会覆盖现有数据。</p>
      <div class="row">
        <button class="btn btn-primary grow" @click="doExport">⬇ 导出备份</button>
        <button class="btn btn-plain grow" @click="$refs.file.click()">⬆ 从文件恢复</button>
        <input ref="file" type="file" accept=".json,application/json" style="display: none" @change="onPickFile" />
      </div>
      <div v-if="restoreInfo" class="restore-info">
        <div class="muted">备份时间：{{ restoreInfo.exported_at || '未知' }}</div>
        <div class="muted">包含模块：{{ restoreInfo.moduleText }}</div>
        <div class="row" style="margin-top: 10px">
          <span class="grow">确认覆盖现有全部数据？</span>
          <button class="btn btn-plain btn-sm" @click="restoreInfo = null">取消</button>
          <button class="btn btn-danger btn-sm" @click="doRestore">确认恢复</button>
        </div>
      </div>
    </div>

    <!-- ============ 清空数据 ============ -->
    <div class="card section danger-section">
      <div class="section-title">清空数据</div>
      <p class="muted sec-hint">勾选要清空的模块（设置将恢复默认值）。此操作不可撤销，建议先导出备份。</p>
      <label class="check-row all-row">
        <input v-model="clearAll" type="checkbox" @change="clearAll && (clearModules = [])" />
        <span>全部清空（保留设置项）</span>
      </label>
      <div class="check-grid" v-if="!clearAll">
        <label v-for="m in CLEAR_MODULES" :key="m.key" class="check-row">
          <input v-model="clearModules" type="checkbox" :value="m.key" />
          <span>{{ m.label }}</span>
        </label>
      </div>
      <template v-if="clearAll || clearModules.length">
        <div class="field" style="margin-top: 12px">
          <label class="field-label">请输入「清空」以确认</label>
          <input v-model="clearConfirmText" class="input" placeholder="清空" />
        </div>
        <button class="btn btn-danger" :disabled="clearConfirmText !== '清空'" @click="doClear">执行清空</button>
      </template>
    </div>

    <!-- ============ 系统信息 ============ -->
    <div class="card section">
      <div class="section-title">系统信息</div>
      <div class="info-row"><span class="muted">版本</span><span>v{{ sysInfo.version }}</span></div>
      <div class="info-row"><span class="muted">数据目录</span><span class="info-val">{{ sysInfo.data_dir }}</span></div>
      <div class="info-row"><span class="muted">本机访问</span><span>http://localhost:{{ sysInfo.port }}</span></div>
      <div class="info-row"><span class="muted">局域网访问</span><span>http://{{ sysInfo.lan_ip }}:{{ sysInfo.port }}</span></div>
      <p class="muted sec-hint">手机需与电脑连同一 Wi-Fi，用浏览器打开局域网地址。</p>
    </div>

    <ConfirmDialog :open="confirmOpen" title="操作确认" :message="confirmMsg"
      :confirm-text="confirmText" :danger="confirmDanger" @confirm="confirmOk" @cancel="confirmOpen = false" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, pad } from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { useSettingsStore } from '../stores/settings'
import { showToast } from '../stores/toast'

const CLEAR_MODULES = [
  { key: 'tasks', label: '今日计划' },
  { key: 'memos', label: '备忘录' },
  { key: 'projects', label: '项目' },
  { key: 'bugs', label: 'Bug 记录' },
  { key: 'notes', label: '笔记' },
  { key: 'workout_plan', label: '健身计划表' },
  { key: 'workout_logs', label: '训练打卡' },
  { key: 'body', label: '身体数据' },
  { key: 'diet', label: '饮食记录' },
  { key: 'events', label: '娱乐日程' },
]

const settings = useSettingsStore()
const stats = ref({})
const sysInfo = ref({})
const form = reactive({ calorie_target: 2000, default_rest_seconds: 60 })

const restoreInfo = ref(null) // { payload, exported_at, moduleText }
const clearAll = ref(false)
const clearModules = ref([])
const clearConfirmText = ref('')

const confirmOpen = ref(false)
const confirmMsg = ref('')
const confirmText = ref('确认')
const confirmDanger = ref(true)
let confirmAction = null

const nextEventText = computed(() => {
  const e = stats.value.next_event
  return e ? e.title : '—'
})

onMounted(async () => {
  stats.value = await api.get('/stats')
  sysInfo.value = await api.get('/system/info')
  await settings.fetch()
  form.calorie_target = settings.calorie_target
  form.default_rest_seconds = settings.default_rest_seconds
})

async function saveSettings() {
  if (!form.calorie_target || form.calorie_target < 1) {
    showToast('热量目标须大于 0', 'error')
    return
  }
  if (form.default_rest_seconds == null || form.default_rest_seconds < 0) {
    showToast('组休秒数须 ≥ 0', 'error')
    return
  }
  await settings.save({
    calorie_target: form.calorie_target,
    default_rest_seconds: form.default_rest_seconds,
  })
  showToast('设置已保存', 'success')
}

// ---- 备份导出 ----
async function doExport() {
  try {
    const res = await fetch('/api/backup/export')
    if (!res.ok) throw new Error()
    const blob = await res.blob()
    const d = new Date()
    const ts = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `life-app-backup-${ts}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('备份已导出', 'success')
  } catch {
    showToast('导出失败', 'error')
  }
}

// ---- 恢复 ----
function onPickFile(ev) {
  const file = ev.target.files[0]
  ev.target.value = ''
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const payload = JSON.parse(reader.result)
      if (payload.app !== 'life-app' || payload.version !== 1 || !payload.data) {
        showToast('不是有效的 life-app 备份文件', 'error')
        return
      }
      const moduleText = Object.entries(payload.data)
        .map(([k, v]) => `${k}(${Array.isArray(v) ? v.length : '…'})`)
        .join('、')
      restoreInfo.value = { payload, exported_at: payload.exported_at, moduleText }
    } catch {
      showToast('文件解析失败', 'error')
    }
  }
  reader.readAsText(file)
}

async function doRestore() {
  const payload = restoreInfo.value.payload
  restoreInfo.value = null
  confirmMsg.value = '恢复将覆盖现有全部数据，确定继续吗？'
  confirmText.value = '确认恢复'
  confirmDanger.value = true
  confirmAction = async () => {
    await api.post('/backup/restore', payload)
    window.location.reload()
  }
  confirmOpen.value = true
}

// ---- 清空 ----
async function doClear() {
  const modules = clearAll.value ? 'all' : [...clearModules.value]
  const names = clearAll.value
    ? '全部数据（保留设置）'
    : CLEAR_MODULES.filter((m) => clearModules.value.includes(m.key)).map((m) => m.label).join('、')
  confirmMsg.value = `将清空：${names}，且不可恢复，确定吗？`
  confirmText.value = '执行清空'
  confirmDanger.value = true
  confirmAction = async () => {
    await api.post('/data/clear', { modules })
    clearAll.value = false
    clearModules.value = []
    clearConfirmText.value = ''
    stats.value = await api.get('/stats')
  }
  confirmOpen.value = true
}

async function confirmOk() {
  confirmOpen.value = false
  await confirmAction()
  showToast('操作完成', 'success')
}
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--sp-3);
  margin-bottom: var(--sp-4);
}

.stat-card {
  text-align: center;
  padding: var(--sp-4) var(--sp-2);
}

.stat-num {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--c-primary);
  margin-bottom: 2px;
  word-break: break-all;
}

.section {
  margin-bottom: var(--sp-4);
}

.section-title {
  font-weight: 600;
  margin-bottom: var(--sp-3);
}

.sec-hint {
  font-size: var(--fs-sm);
  margin-bottom: var(--sp-3);
}

.restore-info {
  margin-top: var(--sp-3);
  padding: var(--sp-3);
  border-radius: var(--r-md);
  background: var(--c-bg);
}

.check-row {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: 6px 0;
  cursor: pointer;
}

.all-row {
  font-weight: 500;
  margin-bottom: var(--sp-2);
}

.check-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
}

.danger-section {
  border: 1px solid var(--c-danger-weak);
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: 6px 0;
  font-size: var(--fs-sm);
  border-bottom: 1px dashed var(--c-line);
}

.info-row:last-of-type {
  border-bottom: none;
}

.info-val {
  word-break: break-all;
  text-align: right;
}
</style>
