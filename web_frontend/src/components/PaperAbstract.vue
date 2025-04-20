<template>
  <v-container fluid class="pr-7">

    <v-card v-if="paper">
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
import { ref, inject } from 'vue';

const paper = inject('paper');

</script>

<style scoped>
</style>