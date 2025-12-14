import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SurveyView from '@/views/SurveyView.vue'
import MissionsView from '@/views/MissionsView.vue'
import CommunauteView from '@/views/CommunauteView.vue'
import ConseilsView from '@/views/ConseilsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import Questions from '@/views/Questions.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/questionnaires',
      name: 'questionnaires',
      component: SurveyView,
    },
    {
      path: '/missions',
      name: 'missions',
      component: MissionsView,
    },
    {
      path: '/communaute',
      name: 'communaute',
      component: CommunauteView,
    },
    {
      path: '/conseils',
      name: 'conseils',
      component: ConseilsView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
    },
    {
      path: '/questionnaires/:category',
      name: 'questionnaire',
      component: () => import('../views/Questions.vue'),
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/:catchAll(.*)',
      name: 'not-found',
      component: () => import('../views/NotFound.vue'),
    },
  ],
})

export default router
