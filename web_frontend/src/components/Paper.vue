<template>
  <v-container fluid>

    <!-- Header  -->
    <v-app-bar>
      <template v-slot:prepend>
        <v-btn icon="mdi-home" href="/"></v-btn>
      </template>
      <v-app-bar-title v-if="paper">{{ paper.title }}</v-app-bar-title>
      <v-app-bar-title v-else>Paper: Loading...</v-app-bar-title>
      <template v-slot:append v-if="paper">
        <v-btn prepend-icon="mdi-graph" :href="`/graph/${paper.id}`">Graph</v-btn>
        <v-btn prepend-icon="mdi-file-pdf-box" :href="`https://arxiv.org/abs/${paper.id}`" target="_blank">arXiv</v-btn>
      </template>
    </v-app-bar>

    <!-- Status Overlay -->
    <div class="status-overlay" v-if="statusMessage">
      <div class="overlay-content">
        <div>{{ statusMessage }}</div>
        <v-btn :onclick="clearStatus" v-if="statusShowClose" variant="tonal" prepend-icon="mdi-close">Close</v-btn>
      </div>
    </div>

    <!-- Paper Details -->
    <v-card v-if="paper" class="mt-5">
      <v-card-title>{{ paper.title }}</v-card-title>
      <v-card-subtitle>
        <p>{{ paper.authors }}</p>
        <p>{{ paper.update_date }} / {{ paper.categories.map(c => c.category).join(', ') }}</p>
      </v-card-subtitle>
      <v-card-text>
        {{ paper.abstract }}
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import * as d3 from 'd3';
import { onMounted, ref, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const initialPaperId = route.params.id;

const paper = ref(null);

const statusMessage = ref("");
const statusShowClose = ref(false);

function clearStatus() {
  statusMessage.value = "";
  statusShowClose.value = false;
}
function showErrorStatus(msg = "Error", error_obj = null) {
  console.error(msg, error_obj);
  if (error_obj) {
    msg += `: ${error_obj}`;
  }
  statusMessage.value = msg;
  statusShowClose.value = true;
}

async function loadData(id) {
  statusMessage.value = "Loading data, please wait...";

  try {
    const response = await fetch('http://localhost:3001/paper_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: id,
      }),
    });

    if (!response.ok) {
      showErrorStatus('Data Loading Response NOT OK', response.status);
      return;
    }

    const result = await response.json();
    statusMessage.value = "";

    console.log('API Result:', result);
    paper.value = result;

  } catch (error) {
    showErrorStatus('Catched Error', error);
  }
}

onMounted(() => {
  loadData(initialPaperId)
});
</script>

<style scoped>
.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(106, 97, 73, 0.343);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  color: white;
  font-size: 1.5rem;
}

.overlay-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 40%;
}

.overlay-content button {
  width: 100px;
}
</style>