import { createRouter, createWebHistory, RouterView } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SurveyView from '@/views/SurveyView.vue'
import MissionsView from '@/views/MissionsView.vue'
import CommunauteView from '@/views/CommunauteView.vue'
import ConseilsView from '@/views/ConseilsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import TrophiesView from '@/views/TrophiesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      // Regroupement Questionnaires
      path: '/questionnaires',
      component: RouterView, // Composant "pass-through" pour afficher les enfants
      children: [
        {
          path: '', // Chemin par défaut (/questionnaires)
          name: 'questionnaires',
          component: SurveyView,
        },
        {
          path: ':category', // Sous-chemin (/questionnaires/:category)
          name: 'questionnaire',
          component: () => import('../views/QuestionsView.vue'),
        },
      ],
    },
    {
      // Regroupement Missions
      path: '/missions',
      component: RouterView,
      children: [
        {
          path: '',
          name: 'missions',
          component: MissionsView,
        },
        {
          path: ':category',
          name: 'mission-category',
          component: () => import('../views/MissionCategoryView.vue'),
        },
      ],
    },
    {
      // Regroupement Communauté
      path: '/communaute',
      component: RouterView,
      children: [
        {
          path: '',
          name: 'communaute',
          component: CommunauteView,
        },
        {
          path: 'amis',
          name: 'CommunityFriends',
          component: () => import('../views/FriendsView.vue'),
        },
        {
          path: 'amis/ajouter',
          name: 'CommunityFriendsAdd',
          component: () => import('../views/AddFriendView.vue'),
        },
        {
          path: 'ligues',
          name: 'CommunityLeagues',
          component: () => import('../views/LeaguesView.vue'),
        },
        {
          path: 'evenements',
          name: 'CommunityEvents',
          component: () => import('../views/EvenementsView.vue'),
        },
      ],
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
      path: '/trophees',
      name: 'trophees',
      component: TrophiesView,
    },
    {
      path: '/about',
      name: 'about',
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
