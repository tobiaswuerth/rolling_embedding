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

            <v-card class="bg-indigo-lighten-1">
              <v-card-text v-if="aiSummary">
                <template v-for="(summary, index) in aiSummary.summaries" :key="index">
                  <div style="text-wrap: wrap;">
                    • {{ summary }}
                  </div>
                </template>
              </v-card-text>
              <v-card-actions v-else>
                <v-btn prepend-icon="mdi-brain" variant="outlined" @click="generateAISummary"
                  :loading="isGeneratingAISummary" :disabled="isGeneratingAISummary">Generate Summary</v-btn>
              </v-card-actions>
            </v-card>
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
import '../lib/tree.js-master/tree.js';
import '../lib/tree.js-master/tree.css';
import { onMounted, ref, inject } from 'vue';
import { useRouter, useRoute } from 'vue-router';
const router = useRouter();
const route = useRoute();

const { hideOverlay, showOverlay } = inject('overlay');
const paperId = inject('paperId');
const paper = inject('paper');
const paperDetails = inject('paperDetails');
const selectedChapter = ref(null);

let tree = null;

const isGeneratingAISummary = ref(false);
const aiSummary = ref(null);
const aiSummaries = ref({});

async function generateAISummary() {
  if (isGeneratingAISummary.value || aiSummary.value) {
    return;
  }

  const chapter = findChapterByPath(route.params.chapterPath);
  if (!chapter) {
    showOverlay('Chapter not found', true);
    return;
  }

  if (aiSummaries.value[chapter.data.text]) {
    aiSummary.value = aiSummaries.value[chapter.data.text];
    return;
  }

  isGeneratingAISummary.value = true;
  try {
    const result = await fetch('http://localhost:3001/generate_chapter_summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: paperId,
        chapter: chapter.data.text,
      }),
    });

    const data = await result.json();
    console.log(data);
    if (!result.ok) {
      throw new Error(data.error);
    }
    aiSummary.value = data;
    aiSummaries.value[chapter.data.text] = data;
    updateMathJax();
  } catch (error) {
    showOverlay('Error generating AI summary', true, error);
  } finally {
    isGeneratingAISummary.value = false;
  }
}

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

function getTreeElement() {
  return document.getElementById('tree');
}

function setupTree() {
  tree = new Tree(getTreeElement());
  // tree.on('open', e => console.log('event "open"', e));
  // tree.on('action', e => console.log('event "action"', e));
  // tree.on('fetch', e => console.log('event "fetch"', e));
  // tree.on('browse', e => console.log('event "browse"', e));
  tree.on('select', e => {
    // console.log('select', e.tagName, e);
    if (e.tagName.toLowerCase() === 'summary') {
      const isOpen = e.parentElement.open;
      setTimeout(() => {
        if (!isOpen && !e.parentElement.open) {
          tree.open(e.parentElement);
        }
      }, 100);
    }

    const hierarchy = tree.hierarchy(e);
    let lookingFor = hierarchy.pop().textContent;
    let chapter = paperDetails.value.find(entry => entry.data.text === lookingFor);

    while (hierarchy.length > 0) {
      lookingFor = hierarchy.pop().textContent;
      chapter = chapter.children.find(entry => entry.data.text === lookingFor);
    }
    selectedChapter.value = chapter;
    aiSummary.value = aiSummaries.value[chapter.data.text] || null;
    updateMathJax();

    // Update the URL with the selected chapter path
    const chapterPath = findChapterPath(paperDetails.value, chapter);
    if (chapterPath) {
      router.replace({
        name: route.name,
        params: {
          ...route.params,
          chapterPath: chapterPath.join('.')
        }
      });
    }
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

function findChapterPath(chapters, targetChapter, currentPath = []) {
  for (let i = 0; i < chapters.length; i++) {
    if (chapters[i] === targetChapter) {
      return [...currentPath, i];
    }

    if (chapters[i].children && chapters[i].children.length > 0) {
      const childPath = findChapterPath(
        chapters[i].children.filter(child => child.type === 'chapter'),
        targetChapter,
        [...currentPath, i]
      );
      if (childPath) {
        return childPath;
      }
    }
  }
  return null;
}

function updateMathJax() {
  setTimeout(() => {
    if (!window.MathJax || !window.MathJax.startup) {
      console.warn('MathJax not available yet, will retry later');
      setTimeout(updateMathJax, 100);
      return;
    }

    try {
      if (!window.MathJax.startup.document) {
        console.warn('MathJax document not ready, will retry');
        setTimeout(updateMathJax, 100);
        return;
      }

      if (typeof window.MathJax.typesetClear === 'function') {
        try {
          window.MathJax.typesetClear();
        } catch (err) {
          console.warn('Error clearing MathJax:', err);
        }
      }

      const mathContainer = document.querySelector('.mathjax-process');
      if (!mathContainer) {
        console.warn('No .mathjax-process element found');
        return;
      }

      Promise.resolve().then(() => {
        if (window.MathJax.typesetPromise) {
          return window.MathJax.typesetPromise([mathContainer]);
        }
      }).catch(err => {
        console.error('MathJax typesetting error:', err);
      });
    } catch (err) {
      console.error('Error during MathJax processing:', err);
    }
  });
}

function initMathJax() {
  if (window.MathJax) {
    console.log('MathJax already loaded, updating instead');
    updateMathJax();
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
      processEscapes: true,
    },
    svg: {
      fontCache: 'global'
    },
    options: {
      ignoreHtmlClass: 'mathjax-ignore',
      processHtmlClass: 'mathjax-process',
    },
    startup: {
      pageReady: () => {
        console.log('MathJax page is ready');
        return window.MathJax.startup.defaultPageReady().catch(err => {
          console.warn('Error in MathJax pageReady:', err);
        });
      }
    }
  };

  const loadMathJaxScript = () => {
    var script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
    script.async = true;
    script.onload = () => {
      console.log('MathJax loaded successfully');

      const checkMathJaxReady = () => {
        if (window.MathJax && window.MathJax.typesetPromise && window.MathJax.startup && window.MathJax.startup.document) {
          setTimeout(updateMathJax);
        } else {
          console.log('MathJax not fully initialized, waiting...');
          setTimeout(checkMathJaxReady, 100);
        }
      };

      checkMathJaxReady();
    };

    script.onerror = () => console.error('Failed to load MathJax');
    document.head.appendChild(script);
  };

  loadMathJaxScript();
}

function findChapterByPath(path) {
  if (!path || !paperDetails.value) return null;

  try {
    const indices = path.split('.').map(Number);
    let chapters = paperDetails.value;
    let targetChapter = null;

    for (const index of indices) {
      if (!chapters[index]) {
        console.warn(`Chapter at index ${index} not found in path:`, path);
        return null;
      }

      targetChapter = chapters[index];
      chapters = targetChapter.children.filter(child => child.type === 'chapter');
    }

    return targetChapter;
  } catch (e) {
    console.error("Error finding chapter by path:", e);
    return null;
  }
}

function selectChapterByPath(path) {
  const targetChapter = findChapterByPath(path);
  if (!targetChapter) {
    console.warn('No chapter found for path:', path);
    return;
  }

  selectedChapter.value = targetChapter;
  updateMathJax();

  // open tree to this chapter
  const treeElement = getTreeElement();
  const elements = treeElement.querySelectorAll('[data-type="folder"]>summary, [data-type="file"]');
  const selectedElement = Array.from(elements).find(el => el.textContent === targetChapter.data.text);
  if (selectedElement) {
    tree.select(selectedElement);

    // open all parent folders
    let parent = selectedElement.closest('details[data-type="folder"]');
    while (parent) {
      parent.open = true;
      parent = parent.parentElement.closest('details[data-type="folder"]');
    }
  } else {
    console.warn('Selected chapter element not found in tree:', targetChapter.data.text);
  }
}

onMounted(() => {
  initMathJax();
  setupTree();

  if (route.params.chapterPath) {
    selectChapterByPath(route.params.chapterPath);
  } else if (paperDetails.value && paperDetails.value.length > 0) {
    router.replace({
      name: route.name,
      params: {
        ...route.params,
        chapterPath: '0'
      }
    });
    selectedChapter.value = paperDetails.value[0];
  }
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