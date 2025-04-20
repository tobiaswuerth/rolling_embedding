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
    <v-tabs bg-color="indigo-darken-2">
      <v-tab :to="`/paper/${paperId}`" prepend-icon="mdi-text-short" value="abstract">Abstract</v-tab>
      <v-tab :to="`/paper/${paperId}/proc/structure`" prepend-icon="mdi-view-list-outline" value="hierarchy">Structure</v-tab>
      <v-tab :to="`/paper/${paperId}/proc/images`" prepend-icon="mdi-image-outline" value="images">Images</v-tab>
      <v-tab :to="`/paper/${paperId}/graph`" prepend-icon="mdi-graph" value="graph">Similarity Graph</v-tab>
    </v-tabs>
  </v-card>

  <router-view></router-view>
</template>

<script setup>
import { onMounted, ref, provide, inject } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
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

<style scoped>
</style>