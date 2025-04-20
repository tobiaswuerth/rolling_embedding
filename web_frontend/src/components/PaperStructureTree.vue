<template>
  <v-container fluid>
    <v-row>
      <v-col cols="3" style="padding:0;">
        <v-card variant="tonal" :style="{ visibility: paperDetails ? 'visible' : 'hidden' }">
          <v-card-title class="text-h6 font-weight-bold">
            Document Hierarchy
            <v-btn style="float:right;" size="small" density="compact" class="text-red" @click="deleteStructure"
              icon="mdi-delete"></v-btn>
          </v-card-title>
          <v-card-text>
            <div id="tree" class="dark mathjax-ignore"></div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="9" class="mathjax-process" style="padding:0;">
        <v-card v-if="selectedChapter">
          <v-card-title class="text-h6 font-weight-bold">
            {{ selectedChapter.data.text }}
          </v-card-title>
          <v-card-text>
            <v-container fluid>
              <div v-for="(content, index) in selectedChapter.children" :key="index" class="mb-4">
                <div v-if="content.type === 'text' || content.type === 'equation'">
                  {{ content.data.text }}
                </div>
                <div v-else-if="content.type === 'image' || content.type === 'table'">
                  <a v-if="content.data.img_path" :href="getImageUrl(content.data.img_path)" target="_blank">
                    <img :src="getImageUrl(content.data.img_path)" alt="img" class="img-fluid" style="max-width: 100%;"
                      loading="lazy" />
                  </a>
                  <div v-if="content.data.img_caption && content.data.img_caption.length > 0">
                    {{ content.data.img_caption.join(' ') }}
                  </div>
                  <div v-if="content.data.table_caption && content.data.table_caption.length > 0">
                    {{ content.data.table_caption.join(' ') }}</div>
                  <div v-if="content.data.img_footnote && content.data.img_footnote.length > 0">
                    {{ content.data.img_footnote.join(' ') }}</div>
                  <div v-if="content.data.table_footnote && content.data.table_footnote.length > 0">
                    {{ content.data.table_footnote.join(' ') }}</div>
                </div>
                <p v-else-if="content.type === 'chapter'"></p>
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
  </v-container>
</template>

<script setup>
import { onMounted, ref, inject, watch } from 'vue';
import '../lib/tree.js-master/tree.js';
import '../lib/tree.js-master/tree.css';

const { hideOverlay, showOverlay } = inject('overlay');
const paperId = inject('paperId');
const paper = inject('paper');
const paperDetails = inject('paperDetails');
const selectedChapter = ref(null);

function getImageUrl(imgPath) {
  const imgPathEncoded = encodeURIComponent(imgPath);
  return `http://localhost:3001/img/${imgPathEncoded}`;
}

function deleteStructure() {
  const confirmDelete = confirm("Are you sure you want to delete the structure? This will require/allow you to reprocess the paper.");
  if (!confirmDelete) {
    return;
  }

  showOverlay("Deleting structure...");
  fetch('http://localhost:3001/delete_document_by_id', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paper_id: paperId,
    }),
  }).then(response => {
    hideOverlay();
    window.location.reload();
  }).catch(error => {
    showOverlay('Error deleting paper data', true, error);
  });
}

function setupTree() {
  const tree = new Tree(document.getElementById('tree'));

  tree.on('select', e => {
    const hierarchy = tree.hierarchy(e);
    let lookingFor = hierarchy.pop().textContent;
    let chapter = paperDetails.value.find(entry => entry.data.text === lookingFor);

    while (hierarchy.length > 0) {
      lookingFor = hierarchy.pop().textContent;
      chapter = chapter.children.find(entry => entry.data.text === lookingFor);
    }
    console.log(chapter);
    selectedChapter.value = chapter;
    updateMathJax();
  });

  function _createStructureEntry(entry) {
    const subChapters = entry.children.filter(e => e.type === 'chapter');
    return {
      name: entry.data.text,
      type: subChapters.length > 0 ? Tree.FOLDER : Tree.FILE,
      selected: false,
      open: false,
      children: subChapters.map(_createStructureEntry),
    }
  }

  const structure = paperDetails.value
    .filter(e => e.type === 'chapter' && e.children.length > 0)
    .map(_createStructureEntry);
  tree.json(structure);
}

function updateMathJax() {
  setTimeout(() => {
    window.MathJax.startup.promise.then(() => {
      window.MathJax.typesetPromise().catch(console.error);
    }).catch(console.error);
  });
}

function initMathJax() {
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
  setupTree();
});
</script>

<style scoped></style>

<style>
.MathJax {
  background-color: #4b4642;
  padding: 1px;
  border-radius: 5px;
  font-size: 1rem;
  overflow: auto;
}
</style>