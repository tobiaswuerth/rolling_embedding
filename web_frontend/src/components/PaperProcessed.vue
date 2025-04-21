<template>
  <template v-if="paper && (!is_downloaded || !is_processed || !is_structurized)">
    <v-container>
      <v-card class="bg-red text-black">
        <v-card-title>
          Action required
        </v-card-title>
        <v-card-text>
          To use this function, you need to download and process the PDF
        </v-card-text>
        <v-card-actions v-if="!processRunning">
          <v-btn variant="tonal" size="small" v-if="!is_downloaded" @click="downloadPDF"
            :class="is_downloaded ? `bg-green` : `bg-black`" prepend-icon="mdi-download">
            Download PDF
          </v-btn>
          <v-btn variant="tonal" size="small" v-else-if="!is_processed" @click="processPDF"
            :class="is_processed ? `bg-green` : `bg-black`" prepend-icon="mdi-cog-play">
            Process PDF
          </v-btn>
          <v-btn variant="tonal" size="small" v-else-if="!is_structurized" @click="structurizePDF"
            :class="is_structurized ? `bg-green` : `bg-black`" prepend-icon="mdi-car-shift-pattern">
            Structure PDF
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
  <template v-if="paperDetails && is_downloaded && is_processed && is_structurized">
    <router-view></router-view>
  </template>
</template>

<script setup>
import { io } from "socket.io-client";
import { ref, inject, provide, watch } from 'vue';

const { hideOverlay, showOverlay } = inject('overlay');
const paperId = inject('paperId');
const paper = inject('paper');
const is_downloaded = inject('is_downloaded');
const is_processed = inject('is_processed');
const is_structurized = inject('is_structurized');

const paperDetails = ref(null);
provide('paperDetails', paperDetails);

const processRunning = ref(false);
const processStatuses = ref([]);

async function emitProcessRequest(event_name) {
  processRunning.value = true;

  processStatuses.value.push({
    message: "Connecting to backend...",
    done: false,
  });

  return new Promise((resolve, reject) => {
    const socket = io("http://localhost:3001");

    socket.on("connect", () => {
      console.log("Connected to server");
      processStatuses.value[processStatuses.value.length - 1].done = true;

      processStatuses.value.push({
        message: `Sending request for ${event_name}...`,
        done: false,
      });
      socket.emit(event_name, { paper_id: paperId });
      processStatuses.value[processStatuses.value.length - 1].done = true;
    });
    socket.on("progress", (data) => {
      console.log(data);
      processStatuses.value[processStatuses.value.length - 1].done = true;
      if (data.status === "OK") {
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
        message: `Process ${event_name} completed, disconnecting...`,
        done: false,
      });
      socket.disconnect();
      processStatuses.value[processStatuses.value.length - 1].done = true;
      processRunning.value = false;

      resolve();
    });

    function _handleError(error) {
      console.error(error);
      processRunning.value = false;
      processStatuses.value = [];
      showOverlay("Error: " + error.message, true, error);
      reject(error);
    }
    socket.on("connect_error", _handleError);
    socket.on("error", _handleError);
  });
}

function downloadPDF() {
  emitProcessRequest("paper_1_download").then(() => {
    is_downloaded.value = true;
    processPDF();
  });
}
function processPDF() {
  emitProcessRequest("paper_2_process").then(() => {
    is_processed.value = true;
    structurizePDF();
  });
}
function structurizePDF() {
  emitProcessRequest("paper_3_structurize").then(() => {
    is_structurized.value = true;
    window.location.reload();
  });
}

async function loadDataProcessed() {
  showOverlay("Loading paper structure...");

  try {
    const response = await fetch('http://localhost:3001/load_document_by_id', {
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
    paperDetails.value = result.contents.children;
    hideOverlay();
  } catch (error) {
    showOverlay('Error loading paper data', true, error);
  }
}

watch([is_downloaded, is_processed, is_structurized], (newValue) => {
  if (is_downloaded.value && is_processed.value && is_structurized.value) {
    loadDataProcessed();
  }
}, { immediate: true });

</script>

<style scoped></style>