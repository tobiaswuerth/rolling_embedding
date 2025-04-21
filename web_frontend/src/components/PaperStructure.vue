<template>

  <v-card>
    <v-tabs v-model="activeTab" bg-color="indigo-darken-2">
      <v-tab @click="navigateTo(`/paper/${paperId}/$$/structure`)" prepend-icon="mdi-car-shift-pattern"
        value="tree">Tree</v-tab>
      <v-tab @click="navigateTo(`/paper/${paperId}/$$/structure/map`)" prepend-icon="mdi-grid" value="map">Map</v-tab>
    </v-tabs>
  </v-card>

  <router-view></router-view>
</template>

<script setup>
import { inject, computed } from 'vue';
import { useRoute } from 'vue-router';

const paperId = inject('paperId');

const route = useRoute();
const navigateTo = inject('navigateTo');
const activeTab = computed(() => {
  return route.path.endsWith('/map') ? 'map' : 'tree';
});

</script>