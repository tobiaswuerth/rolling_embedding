<template>
  <v-app>

    <!-- Status Overlay -->
    <div class="status-overlay" v-if="overlayText">
      <div class="overlay-content">
        <div>{{ overlayText }}</div>
        <v-btn @click="hideOverlay" v-if="overlayShowClose" variant="tonal" prepend-icon="mdi-close">Close</v-btn>
      </div>
    </div>

    <!-- MainView -->
    <v-main>
      <router-view />
    </v-main>

    <AppFooter />
  </v-app>
</template>

<script setup>
import { ref, provide } from 'vue';
import { useRouter } from 'vue-router';
import AppFooter from './components/AppFooter.vue';

const router = useRouter();
function navigateTo(path) {
  router.push(path);
}
provide('navigateTo', navigateTo);

const overlayText = ref("");
const overlayShowClose = ref(false);

function hideOverlay() {
  overlayText.value = "";
  overlayShowClose.value = false;
}

function showOverlay(msg, showClose = false, data_obj = null) {
  if (data_obj) {
    console.log(msg, data_obj);
  } else {
    console.log(msg);
  }

  overlayText.value = data_obj ? msg + `: ${JSON.stringify(data_obj)}` : msg;
  overlayShowClose.value = showClose;
}
provide('overlay', { hideOverlay, showOverlay });

</script>

<style scoped>
.status-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(90, 74, 46, 0.637);
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