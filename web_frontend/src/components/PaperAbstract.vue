<template>
  <v-container fluid class="pr-7">
    <!-- Status Overlay -->
    <div class="status-overlay" v-if="statusMessage">
      <div class="overlay-content">
        <div>{{ statusMessage }}</div>
        <v-btn :onclick="clearStatus" v-if="statusShowClose" variant="tonal" prepend-icon="mdi-close">Close</v-btn>
      </div>
    </div>

    <!-- Paper Summary -->
    <v-card v-if="paper" class="">
      <v-card-title>{{ paper.title }}</v-card-title>
      <v-card-subtitle>
        <p>{{ paper.authors }}</p>
        <p>{{ paper.update_date }} / {{paper.categories.map(c => c.category).join(', ')}}</p>
      </v-card-subtitle>
      <v-card-text>
        {{ paper.abstract }}
      </v-card-text>
    </v-card>

  </v-container>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';


const route = useRoute();
const paperId = route.params.id;

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

async function loadData() {
  statusMessage.value = "Loading data, please wait...";

  try {
    const response = await fetch('http://localhost:3001/paper_by_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: paperId,
      }),
    });

    if (!response.ok) {
      showErrorStatus('Data Loading Response NOT OK', response.status);
      return;
    }

    const result = await response.json();
    statusMessage.value = "";

    console.log('API Result:', result);
    paper.value = result.paper;

  } catch (error) {
    showErrorStatus('Catched Error', error);
  }
}

onMounted(() => {
  loadData()
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