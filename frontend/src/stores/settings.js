import { defineStore } from 'pinia'
import { api } from '../api'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    calorie_target: 2000,
    default_rest_seconds: 60,
    loaded: false,
  }),
  actions: {
    async fetch() {
      const s = await api.get('/settings')
      this.calorie_target = s.calorie_target
      this.default_rest_seconds = s.default_rest_seconds
      this.loaded = true
    },
    async save(patch) {
      const s = await api.put('/settings', patch)
      this.calorie_target = s.calorie_target
      this.default_rest_seconds = s.default_rest_seconds
    },
  },
})
