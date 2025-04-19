<template>
  <template v-if="paper && (!is_downloaded || !is_processed)">
    <v-container>
      <v-card class="bg-red text-black">
        <v-card-title>
          Action required
        </v-card-title>
        <v-card-text>
          To use this function, you need to download and process the PDF
        </v-card-text>
        <v-card-actions v-if="!processRunning">
          <v-btn class="bg-black" variant="tonal" @click="downloadPDF" prepend-icon="mdi-download" size="small"
            v-if="!is_downloaded">
            Download and Process PDF
          </v-btn>
          <v-btn class="bg-black" variant="tonal" @click="processPDF" prepend-icon="mdi-cog-play" size="small"
            v-if="!is_processed && is_downloaded">
            Process PDF
          </v-btn>
        </v-card-actions>
      </v-card>

      <v-container v-if="processRunning">
        <v-list class="status-list">
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
      </v-container>

    </v-container>
  </template>
  <template v-if="paper && is_downloaded && is_processed">
    <router-view></router-view>
  </template>
</template>

<script setup>
import { io } from "socket.io-client";
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const paperId = route.params.id;
const paper = ref(null);
const is_downloaded = ref(false);
const is_processed = ref(false);

const processRunning = ref(false);
const processStatuses = ref([]);


async function processPDF() {
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
    is_processed.value = true;
  });

  socket.on("error", (error) => {
    console.error(error);
    processRunning.value = false;
    processStatuses.value.push({
      message: "Error: " + error.message,
      done: true,
    });
  });
}

async function downloadPDF() {
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
    is_downloaded.value = true;
    is_processed.value = true;
  });

  socket.on("error", (error) => {
    console.error(error);
    processRunning.value = false;
    processStatuses.value.push({
      message: "Error: " + error.message,
      done: true,
    });
  });
}

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
    is_downloaded.value = result.is_downloaded;
    is_processed.value = result.is_processed;
  } catch (error) {
    console.error('Caught Error', error);
  }
}

onMounted(() => {
  loadData()
});
</script>

<style scoped></style>