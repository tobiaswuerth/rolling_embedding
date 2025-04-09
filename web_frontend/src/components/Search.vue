<template>
  <v-container class="py-8">
    <v-responsive class="mx-auto" max-width="900">
      <v-img class="mb-4" height="150" src="@/assets/logo.png" />

      <div class="text-center mb-6">
        <h1 class="text-h2 font-weight-bold">arXiv Search</h1>
      </div>

      <v-row>

        <v-col cols="9">
          <v-text-field v-model="search" label="What are you looking for?" prepend-inner-icon="mdi-magnify"
            variant="outlined" rounded="lg" clearable hide-details @keydown.enter="onSearch" :loading="show_loading" />
        </v-col>
        <v-col cols="3">
          <v-checkbox label="Exact Match" v-model="exact_match"></v-checkbox>
        </v-col>
      </v-row>

      <v-row v-if="results.length > 0" dense>
        <v-col v-for="(item, index) in results" :key="index" cols="12" sm="6" md="4">
          <v-card class="h-100 d-flex flex-column" elevation="2" rounded="xl">
            <v-card-title class="text-h6 font-weight-bold" style="white-space: normal;">
              {{ item._source.title }}
            </v-card-title>
            <v-card-subtitle class="d-flex flex-wrap gap-1">
              <span class="text-caption" style="white-space: normal;">
                {{ item._source.authors }}
              </span>
            </v-card-subtitle>
            <v-card-text class="text-body-2 line-clamp">
              {{ item._source.abstract }}
            </v-card-text>
            <v-spacer />
            <v-card-actions>
              <v-btn :href="`https://arxiv.org/pdf/${item._source.id}`" target="_blank" variant="tonal" density="compact" prepend-icon="mdi-file-pdf-box">
                View PDF
              </v-btn>
              <v-btn :href="`/graph/${item._source.id}`" variant="tonal" density="compact" prepend-icon="mdi-graph">
                Graph
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-responsive>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const search = ref('')
const results = ref([])
const show_loading = ref(false)
const exact_match = ref(true)

async function onSearch() {
  show_loading.value = true;

  const endpoint = exact_match.value ? 'search_by_text' : 'search_by_embedding';
  console.log(endpoint)

  const response = await fetch(`http://localhost:3001/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: search.value,
    }),
  })
  show_loading.value = false;
  if (!response.ok) {
    console.error('Error fetching data:', response.statusText)
    return
  }

  results.value = await response.json()
  console.log(results.value)
}
</script>

<style scoped>
.line-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
