import { createRouter, createWebHistory } from 'vue-router'
import MainPage from '../views/MainPage.vue'
import Home from '../views/Home.vue'
import Spells from '../views/Spells.vue'
import ClassSpells from '../views/ClassSpells.vue'

const routes = [
  {
    path: '/',
    name: 'MainPage',
    component: MainPage
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/spells',
    name: 'Spells',
    component: Spells
  },
  {
    path: '/class/:className',
    name: 'ClassSpells',
    component: ClassSpells,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 