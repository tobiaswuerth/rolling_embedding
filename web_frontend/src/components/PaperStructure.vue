<template>
  <v-container fluid>
    <v-row>
      <v-col cols="3" style="padding:0;">
        <v-card variant="tonal" :style="{ visibility: paperDetails ? 'visible' : 'hidden' }">
          <v-card-title class="text-h6 font-weight-bold">
            Document Hierarchy
          </v-card-title>
          <v-card-text>
            <div id="tree" class="dark mathjax-ignore"></div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="9" class="mathjax-process" style="padding:0;">
        <v-card v-if="selectedChapter">
          <v-card-title class="text-h6 font-weight-bold">
            {{ selectedChapter.title }}
          </v-card-title>
          <v-card-text>
            <v-container fluid>
              <div v-for="(content, index) in selectedChapter.contents" :key="index" class="mb-4">
                <div v-if="content.type === 'text' || content.type === 'equation'">
                  {{ content.text }}
                </div>
                <div v-else-if="content.type === 'image' || content.type === 'table'">
                  <a v-if="content.img_path" :href="getImageUrl(content.img_path)" target="_blank">
                    <img :src="getImageUrl(content.img_path)" alt="img" class="img-fluid" style="max-width: 100%;"
                      loading="lazy" />
                  </a>
                  <div v-if="content.img_caption && content.img_caption.length > 0">
                    {{ content.img_caption.join(' ') }}
                  </div>
                  <div v-if="content.table_caption && content.table_caption.length > 0">
                    {{ content.table_caption.join(' ') }}</div>
                  <div v-if="content.img_footnote && content.img_footnote.length > 0">
                    {{ content.img_footnote.join(' ') }}</div>
                  <div v-if="content.table_footnote && content.table_footnote.length > 0">
                    {{ content.table_footnote.join(' ') }}</div>
                </div>
                <div v-else class="bg-error">
                  <p>Unknown content type: {{ content.type }}</p>
                  {{ content }}
                </div>
              </div>
            </v-container>
          </v-card-text>
        </v-card>
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
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import '../lib/tree.js-master/tree.js';
import '../lib/tree.js-master/tree.css';

const route = useRoute();
const paperId = route.params.id;

const paper = ref(null);
const is_downloaded = ref(false);
const is_processed = ref(false);
const paperDetails = ref(null);

const selectedChapter = ref(null);

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

function getImageUrl(imgPath) {
  const imgPathEncoded = encodeURIComponent(imgPath);
  return `http://localhost:3001/img/${imgPathEncoded}`;
}

function updateMathJax() {
  setTimeout(() => {
    window.MathJax.startup.promise.then(() => {
      window.MathJax.typesetPromise().catch(console.error);
    }).catch(console.error);
  });
}

function setupTree() {
  const tree = new Tree(document.getElementById('tree'));

  tree.on('select', e => {
    const hierarchy = tree.hierarchy(e);
    let lookingFor = hierarchy.pop().textContent;
    let chapter = paperDetails.value.find(entry => entry.title === lookingFor);

    if (hierarchy.length > 0) {
      let lookingFor = hierarchy.pop().textContent;
      chapter = chapter.sub_chapters.find(sub_entry => sub_entry.title === lookingFor);
    }
    selectedChapter.value = chapter;

    updateMathJax();
  });

  const structure = paperDetails.value
    .filter(e => e.contents.length > 0 || e.sub_chapters.length > 0)
    .map(entry => {
      return {
        name: entry.title,
        type: entry.sub_chapters.length > 0 ? Tree.FOLDER : Tree.FILE,
        selected: false,
        open: true,
        children: entry.sub_chapters.map(sub_entry => {
          return {
            name: sub_entry.title,
          }
        }),
      }
    });

  tree.json(structure);
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
    setupTree();

  } catch (error) {
    showErrorStatus('Catched Error', error);
  }
}

function initMathJax() {
  if (window.MathJax) {
    return;
  }
  console.log('Loading MathJax...');
  window.MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      macros: {
        textcircled: ['\\enclose{circle}{#1}', 1],
      },
    },
    svg: {
      fontCache: 'global'
    },
    options: {
      ignoreHtmlClass: 'mathjax-ignore',
      processHtmlClass: 'mathjax-process',
    },
  };
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
  script.async = true;
  script.onload = () => console.log('MathJax loaded successfully');
  script.onerror = () => console.error('Failed to load MathJax');
  document.head.appendChild(script);
}

onMounted(() => {
  initMathJax();
  loadDataProcessed();
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

<style>
.MathJax {
  background-color: #4b4642;
  padding: 1px;
  border-radius: 5px;
  font-size: 1rem;
  overflow: auto;
}
</style>