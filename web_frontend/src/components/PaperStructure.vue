<template>

  <v-card>
    <v-tabs bg-color="indigo-darken-2">
      <v-tab :to="`/paper/${paperId}/proc/structure`" prepend-icon="mdi-car-shift-pattern" value="hierarchy">Tree</v-tab>
      <v-tab :to="`/paper/${paperId}/proc/structure/map`" prepend-icon="mdi-grid" value="images">Map</v-tab>
    </v-tabs>
  </v-card>

  <router-view></router-view>
</template>

<script setup>
import { onMounted, ref, inject, watch } from 'vue';

const paperId = inject('paperId');

</script>

<style scoped></style>
