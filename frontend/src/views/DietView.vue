<template>
  <div class="page">
    <!-- 移动端健康分段切换 -->
    <div class="health-seg">
      <router-link to="/fitness" class="hs-item">健身</router-link>
      <router-link to="/diet" class="hs-item active">饮食</router-link>
    </div>

    <div class="row head">
      <h2 class="page-title grow">饮食计划</h2>
      <button class="btn btn-primary" @click="openCreate()">＋ 记录</button>
    </div>

    <DateSwitcher :date="date" @change="date = $event" />

    <!-- 热量卡 -->
    <div class="card calorie-card">
      <div class="row">
        <div>
          <span class="cal-intake">{{ summary.intake }}</span>
          <span class="muted"> / {{ summary.target }} 千卡</span>
        </div>
        <span class="muted">{{ pctText }}</span>
      </div>
      <div class="progress">
        <div class="progress-bar" :class="{ over: overTarget }" :style="{ width: pct + '%' }"></div>
      </div>
      <div class="muted cal-hint">{{ overTarget ? '已超过目标，注意控制' : '今日已摄入 / 全天目标' }}</div>
    </div>

    <!-- 四餐区块 -->
    <div v-for="m in MEALS" :key="m.key" class="meal-group">
      <div class="row meal-head">
        <span class="meal-name">{{ m.label }}</span>
        <span class="muted grow">{{ mealKcal(m.key) ? `${mealKcal(m.key)} 千卡` : '' }}</span>
        <button class="icon-btn" @click="openCreate(m.key)">＋</button>
      </div>

      <div v-for="e in byMeal(m.key)" :key="e.id" class="card diet-item" :class="{ eaten: e.eaten }">
        <Checkbox :model-value="e.eaten" @update:model-value="toggleEaten(e)" />
        <div class="grow item-main">
          <div class="item-name">{{ e.name }}</div>
          <div v-if="e.note" class="muted item-note">{{ e.note }}</div>
        </div>
        <span class="item-kcal">{{ e.calories }} <span class="muted">千卡</span></span>
        <button class="icon-btn" @click="openEdit(e)">✏️</button>
        <button class="icon-btn" @click="askDelete(e)">🗑️</button>
      </div>

      <div v-if="!byMeal(m.key).length" class="muted meal-empty">暂无记录</div>
    </div>

    <!-- 移动端悬浮新建按钮 -->
    <button class="fab" @click="openCreate()">＋</button>

    <Modal :open="formOpen" :title="editing ? '编辑条目' : '记录饮食'" @close="formOpen = false">
      <form @submit.prevent="submit">
        <div class="field">
          <label class="field-label">名称 *</label>
          <input v-model="form.name" class="input" placeholder="吃了什么？" required maxlength="60" />
        </div>
        <div class="row">
          <div class="field grow">
            <label class="field-label">热量（千卡）</label>
            <input v-model.number="form.calories" type="number" min="0" step="1" class="input" placeholder="0" />
          </div>
          <div class="field grow">
            <label class="field-label">餐段</label>
            <select v-model="form.meal" class="select">
              <option v-for="m in MEALS" :key="m.key" :value="m.key">{{ m.label }}</option>
            </select>
          </div>
        </div>
        <div class="field">
          <label class="field-label">日期</label>
          <input v-model="form.date" type="date" class="input" required />
        </div>
        <div class="field">
          <label class="field-label">备注</label>
          <textarea v-model="form.note" class="textarea" maxlength="200"></textarea>
        </div>
        <button class="btn btn-primary btn-block" type="submit">保存</button>
      </form>
    </Modal>

    <ConfirmDialog :open="!!deleting" title="删除条目" :message="`确定删除「${deleting?.name}」吗？`"
      confirm-text="删除" danger @confirm="doDelete" @cancel="deleting = null" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api, todayStr } from '../api'
import Checkbox from '../components/Checkbox.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import DateSwitcher from '../components/DateSwitcher.vue'
import Modal from '../components/Modal.vue'
import { useSettingsStore } from '../stores/settings'
import { showToast } from '../stores/toast'

const MEALS = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' },
  { key: 'snack', label: '加餐' },
]

const settings = useSettingsStore()
const date = ref(todayStr())
const items = ref([])
const summary = ref({ intake: 0, target: 2000, by_meal: {} })
const formOpen = ref(false)
const editing = ref(null)
const deleting = ref(null)
const form = ref({ name: '', calories: null, meal: 'breakfast', date: todayStr(), note: '' })

const pct = computed(() => {
  const t = summary.value.target || 1
  return Math.min(100, Math.round((summary.value.intake / t) * 100))
})
const pctText = computed(() => {
  const t = summary.value.target || 1
  return `${Math.round((summary.value.intake / t) * 100)}%`
})
const overTarget = computed(() => summary.value.intake > summary.value.target)

function byMeal(key) {
  return items.value.filter((e) => e.meal === key)
}

function mealKcal(key) {
  return summary.value.by_meal?.[key] || 0
}

async function load() {
  items.value = await api.get(`/diet?date=${date.value}`)
  summary.value = await api.get(`/diet/summary?date=${date.value}`)
}

watch(date, load)
onMounted(() => {
  settings.fetch()
  load()
})

function openCreate(mealKey) {
  editing.value = null
  form.value = { name: '', calories: null, meal: mealKey || 'breakfast', date: date.value, note: '' }
  formOpen.value = true
}

function openEdit(e) {
  editing.value = e
  form.value = { name: e.name, calories: e.calories, meal: e.meal, date: e.date, note: e.note }
  formOpen.value = true
}

async function submit() {
  const name = form.value.name.trim()
  if (!name) return
  const payload = {
    name,
    calories: form.value.calories != null && form.value.calories >= 0 ? form.value.calories : 0,
    meal: form.value.meal,
    date: form.value.date,
    note: form.value.note.trim(),
  }
  if (editing.value) {
    await api.put(`/diet/${editing.value.id}`, payload)
    showToast('已保存', 'success')
  } else {
    await api.post('/diet', payload)
    showToast('已记录', 'success')
  }
  formOpen.value = false
  await load()
}

async function toggleEaten(e) {
  await api.put(`/diet/${e.id}`, { eaten: !e.eaten })
  await load()
}

function askDelete(e) {
  deleting.value = {
    ...e,
    run: async () => {
      await api.del(`/diet/${e.id}`)
      await load()
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

.calorie-card {
  margin: var(--sp-3) 0 var(--sp-4);
}

.cal-intake {
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--c-primary);
}

.cal-hint {
  font-size: var(--fs-sm);
  margin-top: var(--sp-2);
}

.progress-bar.over {
  background: var(--c-danger);
}

.meal-group {
  margin-bottom: var(--sp-4);
}

.meal-head {
  margin-bottom: var(--sp-2);
}

.meal-name {
  font-weight: 600;
}

.meal-empty {
  font-size: var(--fs-sm);
  padding: 4px 0 0 var(--sp-2);
}

.diet-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-bottom: var(--sp-2);
  padding: var(--sp-3) var(--sp-4);
}

.diet-item.eaten .item-name {
  text-decoration: line-through;
  color: var(--c-text-3);
}

.item-main {
  min-width: 0;
}

.item-name {
  font-weight: 500;
}

.item-note {
  font-size: var(--fs-sm);
  margin-top: 2px;
}

.item-kcal {
  font-size: var(--fs-sm);
  white-space: nowrap;
  font-weight: 500;
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
