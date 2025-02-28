import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard
  },
  {
    path: '/crawler',
    name: 'crawler',
    component: () => import('../views/Crawler.vue')
  },
  {
    path: '/comments',
    name: 'comments',
    component: () => import('../views/Comments.vue')
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('../views/Analysis.vue')
  },
  {
    path: '/articles',
    name: 'articles',
    component: () => import('../views/Articles.vue')
  },
  {
    path: '/articles/:articleId',
    name: 'article-detail',
    component: () => import('../views/ArticleDetail.vue'),
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
