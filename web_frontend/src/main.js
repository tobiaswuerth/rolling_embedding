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


import PaperView from './components/Paper.vue'
import PaperAbstractView from './components/PaperAbstract.vue'
import PaperGraphView from './components/PaperGraph.vue'

import PaperProcessedView from './components/PaperProcessed.vue'
import PaperImagesView from './components/PaperImages.vue'
import PaperStructureView from './components/PaperStructure.vue'
import PaperStructureTreeView from './components/PaperStructureTree.vue'
import PaperStructureMapView from './components/PaperStructureMap.vue'

const routes = [
    {
        path: '/',
        component: SearchView
    },
    {
        path: '/paper/:id([0-9a-zA-Z_\\-\\.]+)',
        component: PaperView,
        children: [
            {
                path: '',
                component: PaperAbstractView,
            },
            {
                path: 'graph',
                component: PaperGraphView,
            },
            {
                path: '$$', // Escaped $$ path
                component: PaperProcessedView,
                children: [
                    {
                        path: 'structure/:chapterPath([0-9\\.]+)?',
                        component: PaperStructureView,
                        children: [
                            {
                                path: '',
                                component: PaperStructureTreeView,
                            },
                            {
                                path: 'map',
                                component: PaperStructureMapView,
                            }
                        ]
                    },
                    {
                        path: 'images',
                        component: PaperImagesView,
                    },
                ],
            },

        ]
    },
]

app.use(createRouter({
    history: createWebHistory(),
    routes,
}))


// finalize
app.mount('#app')
