import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue'), meta: { title: '首页', tab: 'home' } },
  { path: '/today', name: 'today', component: () => import('../views/TodayView.vue'), meta: { title: '今日计划', tab: 'today' } },
  { path: '/dev', name: 'dev', component: () => import('../views/DevView.vue'), meta: { title: '开发工作', tab: 'dev' } },
  { path: '/fitness', name: 'fitness', component: () => import('../views/FitnessView.vue'), meta: { title: '健身计划', tab: 'health' } },
  { path: '/diet', name: 'diet', component: () => import('../views/DietView.vue'), meta: { title: '饮食计划', tab: 'health' } },
  { path: '/entertainment', name: 'entertainment', component: () => import('../views/EntertainmentView.vue'), meta: { title: '游戏娱乐', tab: 'more' } },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { title: '数据与设置', tab: 'more' } },
  { path: '/memos', name: 'memos', component: () => import('../views/MemosView.vue'), meta: { title: '备忘录', tab: 'home' } },
  { path: '/more', name: 'more', component: () => import('../views/MoreView.vue'), meta: { title: '更多', tab: 'more' } },
  { path: '/training', name: 'training', component: () => import('../views/TrainingView.vue'), meta: { title: '训练模式', fullscreen: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 个人工作生活` : '个人工作生活'
})
