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

    <!-- Paper Summary -->
    <v-card v-if="paper" class="mt-5">
      <v-card-title>{{ paper.title }}</v-card-title>
      <v-card-subtitle>
        <p>{{ paper.authors }}</p>
        <p>{{ paper.update_date }} / {{paper.categories.map(c => c.category).join(', ')}}</p>
      </v-card-subtitle>
      <v-card-text>
        {{ paper.abstract }}
      </v-card-text>
      <v-card-actions v-if="!is_downloaded || !is_processed">
        <v-btn variant="tonal" @click="downloadPDF" prepend-icon="mdi-download" size="small" v-if="!is_downloaded">
          Download PDF
        </v-btn>
        <v-btn variant="tonal" @click="processPDF" prepend-icon="mdi-cog-play" size="small"
          v-if="!is_processed && is_downloaded">
          Process PDF
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-list v-if="processRunning" class="status-list">
      <v-divider></v-divider>
      <template v-for="(status, index) in processStatuses" :key="index">
        <v-list-item>
          <template v-if="!status.done">
            <v-progress-circular indeterminate></v-progress-circular>
          </template>
          <template v-else>
            <v-icon class="text-success">mdi-check</v-icon>
          </template>

          {{ status.done ? status.message + ` OK` : status.message }}
        </v-list-item>
        <v-divider></v-divider>
      </template>
    </v-list>

    <template v-if="is_processed && is_downloaded && !processRunning">
      <PaperDetailsView></PaperDetailsView>
    </template>

  </v-container>
</template>

<script setup>
import { io } from "socket.io-client";
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import PaperDetailsView from './PaperDetails.vue';


const route = useRoute();
const paperId = route.params.id;

const paper = ref(null);

const is_downloaded = ref(false);
const is_processed = ref(false);

const processRunning = ref(false);
const processStatuses = ref([]);

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

async function processPDF() {
  is_downloaded.value = true;
  is_processed.value = true;
  processRunning.value = true;

  processStatuses.value.push({
    message: "Connecting to backend...",
    done: false,
  });

  const socket = io("http://localhost:3001");

  socket.on("connect", () => {
    console.log("Connected to server");
    processStatuses.value[0].done = true;

    processStatuses.value.push({
      message: "Requesting to process PDF...",
      done: false,
    });
    socket.emit("process_paper", { paper_id: paperId });
    processStatuses.value[1].done = true;
  });

  socket.on("progress", (data) => {
    console.log(data);

    if (data.status === "OK") {
      processStatuses.value[processStatuses.value.length - 1].done = true;
      return;
    }

    processStatuses.value.push({
      message: data.status,
      done: false,
    });
  });

  socket.on("done", (data) => {
    console.log(data);
    processStatuses.value.push({
      message: "Disconnecting from server...",
      done: false,
    });
    socket.disconnect();
    processStatuses.value[processStatuses.value.length - 1].done = true;
    processRunning.value = false;
  });

  socket.on("error", (error) => {
    console.error(error);
    processRunning.value = false;
    processStatuses.value.push({
      message: "Error: " + error.message,
      done: true,
    });
    is_processed.value = false;
  });
}

async function downloadPDF() {
  is_downloaded.value = true;
  is_processed.value = true;
  processRunning.value = true;

  processStatuses.value.push({
    message: "Connecting to backend...",
    done: false,
  });

  const socket = io("http://localhost:3001");

  socket.on("connect", () => {
    console.log("Connected to server");
    processStatuses.value[0].done = true;

    processStatuses.value.push({
      message: "Requesting to download PDF...",
      done: false,
    });
    socket.emit("download_paper", { paper_id: paperId });
    processStatuses.value[1].done = true;
  });

  socket.on("progress", (data) => {
    console.log(data);

    if (data.status === "OK") {
      processStatuses.value[processStatuses.value.length - 1].done = true;
      return;
    }

    processStatuses.value.push({
      message: data.status,
      done: false,
    });
  });

  socket.on("done", (data) => {
    console.log(data);
    processStatuses.value.push({
      message: "Disconnecting from server...",
      done: false,
    });
    socket.disconnect();
    processStatuses.value[processStatuses.value.length - 1].done = true;
    processRunning.value = false;
  });

  socket.on("error", (error) => {
    console.error(error);
    processRunning.value = false;
    processStatuses.value.push({
      message: "Error: " + error.message,
      done: true,
    });
    is_downloaded.value = false;
    is_processed.value = false;
  });
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
    is_downloaded.value = result.is_downloaded;
    is_processed.value = result.is_processed;

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

.status-list {
  max-width: 500px;
}
</style>