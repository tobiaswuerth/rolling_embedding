import { createApp } from 'vue'
import App from './App.vue'
const app = createApp(App)

// vuetify
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'

app.use(createVuetify({
    theme: {
        defaultTheme: 'dark',
    },
}))

// router
import { createRouter, createWebHistory } from 'vue-router'
import SearchView from './components/Search.vue'
import GraphView from './components/Graph.vue'
import PaperView from './components/Paper.vue'

const routes = [
    {
        path: '/',
        component: SearchView
    },
    {
        path: '/graph/:id(.*)',
        component: GraphView
    },
    {
        path: '/paper/:id(.*)',
        component: PaperView
    },
]

app.use(createRouter({
    history: createWebHistory(),
    routes,
}))


// finalize
app.mount('#app')
