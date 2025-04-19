<template>
  <v-container fluid class="paper-details-container">

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

    <!-- Status Overlay -->
    <div class="status-overlay" v-if="statusMessage">
      <div class="overlay-content">
        <div>{{ statusMessage }}</div>
        <v-btn :onclick="clearStatus" v-if="statusShowClose" variant="tonal" prepend-icon="mdi-close">Close</v-btn>
      </div>
    </div>
  </v-container>
</template>

<script setup>
import { image } from 'd3';
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const paperId = route.params.id;
const paperDetails = ref(null);
const imageUrls = ref([]);

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

function prepareImages() {
  function _getImage(content) {
    const is_img = content.type === "image"
    const is_table = content.type === "table"
    if (is_img || is_table) {
      const imageUrl = 'http://localhost:3001/img/' + encodeURIComponent(content.img_path);
      const imgCaption = is_img ? content.img_caption.join(' ') : content.table_caption.join(' ');
      const imgFootnote = is_img ? content.img_footnote.join(' ') : content.table_footnote.join(' ');
      return { url: imageUrl, caption: imgCaption, footnote: imgFootnote };
    }
    return null;
  }

  paperDetails.value.forEach((chapter) => {
    const imgs = chapter.contents.map(_getImage);
    chapter.sub_chapters.forEach((sub_chapter) => {
      const sub_imgs = sub_chapter.contents.map(_getImage);
      imgs.push(...sub_imgs);
    });
    imgs.filter(Boolean).forEach(x => imageUrls.value.push(x));
  });
}

async function loadDataProcessed() {
  statusMessage.value = "Loading data, please wait...";

  try {
    const response = await fetch('http://localhost:3001/paper_processed_by_id', {
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
    paperDetails.value = result.contents;
    prepareImages();

  } catch (error) {
    showErrorStatus('Catched Error', error);
  }
}

onMounted(() => {
  loadDataProcessed()
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