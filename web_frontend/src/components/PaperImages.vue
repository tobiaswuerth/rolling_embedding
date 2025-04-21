<template>
  <v-container fluid>
    Images
    <v-row>
      <v-col v-for="(e, key) in imageUrls" :key="key" xs="12" sm="6" md="4" lg="3" xl="2" xxl="1">
        <div>
          <a :href="e.url" target="_blank">
            <v-img :src="e.url" :alt="e.caption" lazy></v-img>
          </a>
          {{ e.caption }}
          {{ e.footnote }}
        </div>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup>
import { onMounted, ref, inject } from 'vue';

const paperId = inject('paperId');
const paper = inject('paper');
const paperDetails = inject('paperDetails');

const imageUrls = ref([]);

function prepareImages() {
  imageUrls.value = [];

  function _getImage(content) {
    const is_img = content.type === "image"
    const is_table = content.type === "table"
    const imageUrl = 'http://localhost:3001/img/' + encodeURIComponent(content.data.img_path);
    const imgCaption = is_img ? content.data.img_caption.join(' ') : content.data.table_caption.join(' ');
    const imgFootnote = is_img ? content.data.img_footnote.join(' ') : content.data.table_footnote.join(' ');
    return { url: imageUrl, caption: imgCaption, footnote: imgFootnote };
  }

  function _processChapter(chapter) {
    const imgs = chapter.children.filter(c => c.type === 'image' || c.type === 'table').map(_getImage);
    imageUrls.value.push(...imgs);
    const subChapters = chapter.children.filter(c => c.type === 'chapter');
    subChapters.forEach(_processChapter);
  }

  paperDetails.value.forEach(_processChapter);
}

onMounted(() => {
  prepareImages();
});
</script>