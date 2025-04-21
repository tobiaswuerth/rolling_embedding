<template>
  <v-container fluid>
    <div>
      <div>Legend:</div>
      <div ref="legendContainer" class="legend-container"></div>
    </div>
    <div ref="treemapContainer" class="treemap-container"></div>
  </v-container>
</template>

<script setup>
import * as d3 from 'd3';
import { onMounted, ref, inject, reactive } from 'vue';

const navigateTo = inject('navigateTo');
const { hideOverlay, showOverlay } = inject('overlay');
const paperId = inject('paperId');
const paperDetails = inject('paperDetails');

const data = ref({
  name: "doc",
  children: [],
});
const treemapContainer = ref(null);
const legendContainer = ref(null);
const visibleChapters = reactive({});

function getChapterData(chapter, index) {
  if (chapter.children.length === 0) {
    return {
      name: chapter.data.text || chapter.data.img_path || chapter.data.table_caption || chapter.data.img_caption,
      value: chapter.data.text?.length || chapter.data.img_path?.length || chapter.data.table_caption?.length || chapter.data.img_caption?.length,
      chapterIndex: null,
    };
  }
  return {
    name: chapter.data.text,
    children: getAllChapterData(chapter.children),
    chapterIndex: index,
  };
}
function getAllChapterData(chapters) {
  const result = [];
  let index = -1;
  for (const chapter of chapters) {
    if (chapter.type === 'chapter') {
      // match the logic of the tree by hiding certain chapters but keeping index
      index += 1;
      if (chapter.children.length === 0) {
        continue;
      }
    }
    result.push(getChapterData(chapter, index));
  }
  return result;
}

function initChapters() {
  data.value.children.push(...getAllChapterData(paperDetails.value));
  data.value.children.forEach(chapter => {
    visibleChapters[chapter.name] = true;
  });
}

function renderLegend() {
  if (!legendContainer.value || data.value.children.length === 0) {
    return;
  }

  d3.select(legendContainer.value).selectAll("*").remove();

  const width = legendContainer.value.offsetWidth;
  const itemHeight = 25;
  const itemWidth = 120;
  const itemsPerRow = Math.floor(width / itemWidth);
  const rows = Math.ceil(data.value.children.length / itemsPerRow);
  const height = rows * itemHeight - 9;

  const color = d3.scaleOrdinal()
    .domain(data.value.children.map(d => d.name))
    .range(d3.schemeTableau10);

  const svg = d3.select(legendContainer.value)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const legend = svg.selectAll(".legend")
    .data(data.value.children)
    .enter()
    .append("g")
    .attr("class", "legend")
    .attr("transform", (d, i) => {
      const row = Math.floor(i / itemsPerRow);
      const col = i % itemsPerRow;
      return `translate(${col * itemWidth}, ${row * itemHeight})`;
    })
    .style("cursor", "pointer")
    .on("click", (event, d) => {
      visibleChapters[d.name] = !visibleChapters[d.name];
      updateMap();
    });

  // Add colored rectangles
  legend.append("rect")
    .attr("width", 15)
    .attr("height", 15)
    .attr("fill", d => color(d.name))
    .attr("fill-opacity", d => visibleChapters[d.name] ? 0.7 : 0.2)
    .attr("stroke", "black")
    .attr("stroke-width", 0.5);

  // Add text
  legend.append("text")
    .attr("x", 20)
    .attr("y", 12)
    .text(d => {
      const name = d.name || "Untitled";
      return name.length > 15 ? name.substring(0, 12) + "..." : name;
    })
    .style("font-size", "12px")
    .style("font-family", "Arial, sans-serif")
    .style("fill-opacity", d => visibleChapters[d.name] ? 1 : 0.5);
}

function renderTreemap() {
  if (!treemapContainer.value || data.value.children.length === 0) {
    return;
  }

  d3.select(treemapContainer.value).selectAll("*").remove();

  const width = treemapContainer.value.offsetWidth;
  const legendHeight = legendContainer.value ? legendContainer.value.offsetHeight : 0;
  const height = window.innerHeight - treemapContainer.value.getBoundingClientRect().top - legendHeight;

  const color = d3.scaleOrdinal()
    .domain(data.value.children.map(d => d.name))
    .range(d3.schemeTableau10);

  // Filter data based on visibility settings
  const filteredData = {
    name: data.value.name,
    children: data.value.children.filter(d => visibleChapters[d.name])
  };

  const root = d3.hierarchy(filteredData).sum(d => d.value || 0);
  const treemapLayout = d3.treemap().size([width, height]);
  treemapLayout(root);

  const svg = d3.select(treemapContainer.value)
    .append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("width", width)
    .attr("height", height)
    .style("max-width", "100%")
    .style("height", "auto")
    .style("font", "8px sans-serif");

  const leaf = svg.selectAll("g")
    .data(root.leaves())
    .enter()
    .append("g")
    .attr("transform", d => `translate(${d.x0},${d.y0})`)
    .attr("cursor", "pointer")
    .attr("class", "treemap-node") // Add class to the group element for hover effects
    .on("click", (event, d) => {
      const path = [];

      let current = d.data.chapterIndex ? d : d.parent;
      while (current) {
        if (current.data.chapterIndex !== undefined) {
          path.unshift(current.data.chapterIndex);
        }
        current = current.parent;
      }

      const structurePath = path.join('.');
      navigateTo(`/paper/${paperId}/$$/structure/${structurePath}`);
    });

  const format = d3.format(",d");
  leaf.append("title")
    .text(d => {
      let hierarchy = d.ancestors();
      hierarchy.pop(); // root node
      hierarchy = hierarchy.reverse();
      const text_node = hierarchy.pop();
      return `${hierarchy.map(d => d.data.name).join("\n- ")}\n\n${text_node.data.name}`;
    });

  leaf.append("rect")
    .attr("id", (d, i) => `leaf-${i}`)
    .attr("fill", d => {
      let node = d;
      while (node.depth > 1) {
        node = node.parent;
      }
      return color(node.data.name);
    })
    .attr("fill-opacity", 0.7)
    .attr("width", d => d.x1 - d.x0)
    .attr("height", d => d.y1 - d.y0)
    .attr("stroke", "black")
    .attr("stroke-width", 0.2);

  // Add clipPaths to ensure text doesn't overflow
  leaf.append("clipPath")
    .attr("id", (d, i) => `clip-${i}`)
    .append("use")
    .attr("href", (d, i) => `#leaf-${i}`);

  const cellText = leaf.append("text")
    .attr("clip-path", (d, i) => `url(#clip-${i})`)
    .attr("fill", "white");

  cellText.each(function (d) {
    const rectWidth = d.x1 - d.x0;
    const rectHeight = d.y1 - d.y0;
    const minSize = 25;
    if (rectWidth < minSize || rectHeight < minSize) {
      return;
    }

    const node = d3.select(this);
    const words = d.data.name.split(/\s+/);
    const lineHeight = 12;
    const paddingX = 5;
    const paddingY = 12;
    let y = paddingY;
    let line = [];
    let tspan = node.append("tspan")
      .attr("x", paddingX)
      .attr("y", y)
      .attr("font-size", "10px")
      .attr("font-family", "Arial, sans-serif")
      .attr("fill-opacity", 0.7);

    for (let i = 0; i < words.length; i++) {
      line.push(words[i]);
      tspan.text(line.join(" "));
      if (tspan.node().getComputedTextLength() > rectWidth - 2 * paddingX) {
        line.pop();
        tspan.text(line.join(" "));
        line = [words[i]];
        y += lineHeight;
        if (y + lineHeight / 2 > rectHeight) {
          break;
        }
        tspan = node.append("tspan")
          .attr("x", paddingX)
          .attr("y", y)
          .attr("font-size", "10px")
          .attr("font-family", "Arial, sans-serif")
          .attr("fill-opacity", 0.7)
          .text(words[i]);
      }
    }
  });
}

function updateMap() {
  setTimeout(() => {
    renderLegend();
    renderTreemap();
  });
}

onMounted(() => {
  initChapters();
  updateMap();
});

window.addEventListener('resize', () => {
  renderLegend();
  renderTreemap();
});
</script>

<style scoped>
.legend-container {
  width: 100%;
  margin-bottom: 10px;
  background-color: #727272;
  padding: 10px;
  border-radius: 5px;
}

.treemap-container {
  width: 100%;
  border-radius: 5px;
}

:deep(.treemap-node) {
  transition: all 0.2s ease-in-out;
}

:deep(.treemap-node:hover rect) {
  filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.7));
  stroke: white;
  stroke-width: 1px;
}

:deep(.treemap-node:hover text) {
  fill-opacity: 1 !important;
}
</style>
