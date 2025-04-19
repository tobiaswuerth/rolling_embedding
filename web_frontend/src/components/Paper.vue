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
      <v-tabs v-model="tab" bg-color="indigo-darken-2">
        <v-tab :to="`/paper/${paperId}`" prepend-icon="mdi-text-short" value="abstract" >Abstract</v-tab>
        <v-tab :to="`/paper/${paperId}/proc/structure`" prepend-icon="mdi-view-list-outline" value="hierarchy" >Structure</v-tab>
        <v-tab :to="`/paper/${paperId}/proc/images`" prepend-icon="mdi-image-outline" value="images">Images</v-tab>
        <v-tab :to="`/paper/${paperId}/graph`" prepend-icon="mdi-graph" value="graph">Similarity Graph</v-tab>
      </v-tabs>
    </v-card>

    <router-view></router-view>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const paperId = route.params.id;
const paper = ref(null);

async function loadData() {
  try {
    const response = await fetch('http://localhost:3001/paper_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: paperId,
      }),
    });

    if (!response.ok) {
      console.error('Data Loading Response NOT OK', response.status);
      return;
    }

    const result = await response.json();
    console.log('API Result:', result);
    paper.value = result.paper;
  } catch (error) {
    console.error('Caught Error', error);
  }
}

onMounted(() => {
  loadData()
});
</script>

<style scoped>

</style>