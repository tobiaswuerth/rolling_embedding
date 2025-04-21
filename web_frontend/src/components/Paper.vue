<template>
  <v-app-bar>
    <template v-slot:prepend>
      <v-btn icon="mdi-home" href="/"></v-btn>
    </template>
    <v-app-bar-title v-if="paper">{{ paper.title }}</v-app-bar-title>
    <v-app-bar-title v-else>Paper: Loading...</v-app-bar-title>
    <template v-slot:append v-if="paper">
      <v-btn prepend-icon="mdi-file-pdf-box" :href="`https://arxiv.org/abs/${paper.id}`" target="_blank">arXiv</v-btn>
    </template>
  </v-app-bar>

  <v-card>
    <v-tabs v-model="activeTab" bg-color="indigo-darken-4">
      <v-tab @click="navigateTo(`/paper/${paperId}`)" prepend-icon="mdi-text-short" value="abstract">Abstract</v-tab>
      <v-tab @click="navigateTo(`/paper/${paperId}/$$/structure`)" prepend-icon="mdi-view-list-outline"
        value="structure">Structure</v-tab>
      <v-tab @click="navigateTo(`/paper/${paperId}/$$/images`)" prepend-icon="mdi-image-outline"
        value="images">Images</v-tab>
      <v-tab @click="navigateTo(`/paper/${paperId}/graph`)" prepend-icon="mdi-graph" value="graph">Similarity
        Graph</v-tab>
    </v-tabs>
  </v-card>

  <router-view></router-view>
</template>

<script setup>
import { onMounted, ref, provide, inject, computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const navigateTo = inject('navigateTo');

const paperId = route.params.id;

const { hideOverlay, showOverlay } = inject('overlay');
const paper = ref(null);
const is_downloaded = ref(false);
const is_processed = ref(false);
const is_structurized = ref(false);
provide('paperId', paperId);
provide('paper', paper);
provide('is_downloaded', is_downloaded);
provide('is_processed', is_processed);
provide('is_structurized', is_structurized);

const activeTab = computed(() => {
  return route.path.endsWith('/graph') ? 'graph' : route.path.endsWith('/images') ? 'images' : route.path.includes('/structure') ? 'structure' : 'abstract';
});

async function loadData() {
  showOverlay("Loading paper data...");

  try {
    const response = await fetch('http://localhost:3001/paper_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: paperId,
      }),
    });

    const result = await response.json();
    if (!response.ok) {
      showOverlay('Error loading paper data', true, result);
      return;
    }

    console.log('API Result:', result);
    paper.value = result.paper;
    is_downloaded.value = result.is_downloaded;
    is_processed.value = result.is_processed;
    is_structurized.value = result.is_structurized;

    hideOverlay();
  } catch (error) {
    showOverlay('Error loading paper data', true, error);
  }
}

onMounted(() => {
  loadData();
});
</script>
