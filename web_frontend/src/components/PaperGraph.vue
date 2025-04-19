<template>
  <v-container fluid>
    <v-row>
      <v-col cols="3" class="bg-gray">

        <!-- Paper Preview -->
        <v-card class="paper-preview" v-if="currentPaper !== null">
          <v-card-title class="text-h6 font-weight-bold" style="white-space: normal;">
            {{ currentPaper.title }}
          </v-card-title>
          <v-card-subtitle class="d-flex flex-wrap gap-1">
            <div class="text-caption" style="white-space: normal;">
              {{ currentPaper.authors }}
            </div>
          </v-card-subtitle>
          <v-card-text class="line-clamp">
            {{ currentPaper.abstract }}
          </v-card-text>
          <v-spacer />
          <v-card-actions>
            <v-btn :href="`/paper/${currentPaper.id}`" variant="tonal" density="compact"
              prepend-icon="mdi-magnify-expand">
              View
            </v-btn>
            <v-btn :href="`https://arxiv.org/abs/${currentPaper.id}`" target="_blank" variant="tonal" density="compact"
              prepend-icon="mdi-file-pdf-box">
              arXiv
            </v-btn>
          </v-card-actions>
        </v-card>
        <i v-if="currentPaper === null">
          Hover over node to preview
        </i>
      </v-col>

      <v-col cols="9" class="bg-gray">
        <!-- Graph Config -->
        <div class="graph-config">
          <div class="graph-config-row" v-for="item in configItems" :key="item.label">
            <div class="label text-caption">{{ item.label }}</div>
            <v-slider v-model="item.model.value" :min="item.min" :max="item.max" :step="item.step" hide-details
              class="flex-grow-1" thumb-label density="compact" />
          </div>
        </div>

        <!-- Graph SVG -->
        <div ref="graphContainer" class="graph-container"></div>
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
import * as d3 from 'd3';
import { onMounted, ref, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const initialPaperId = route.params.id;
const papers = new Map();
const currentPaper = ref(null);
const queries = new Map();

const statusMessage = ref("");
const statusShowClose = ref(false);

const graphContainer = ref(null);
let graphContent = null; // Container for zooming and panning
let simulation = null;
const links = new Set();
const d3_nodes = ref([]);
const d3_links = ref([]);
let svg = null;
let linkGroup = null;
let nodeGroup = null;

const linkStiffness = ref(0.3);
const linkAttraction = ref(-250);
const configItems = [
  { label: 'Link Stiffness', model: linkStiffness, min: 0.1, max: 1.0, step: 0.1 },
  { label: 'Link Attraction', model: linkAttraction, min: -500, max: 0, step: 10 },
];

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

watch([linkStiffness, linkAttraction], () => {
  if (!simulation) {
    return;
  }

  simulation.force('link').strength(linkStiffness.value);
  simulation.force('charge').strength(linkAttraction.value);
  simulation.alpha(1).restart();
});

function getConnectionCount(d) {
  return d3_links.value.filter(l => l.source.id === d.id || l.target.id === d.id).length;
}
function getNodeLabel(d, short = true) {
  let label = d.label;
  if (short && d.label.length > 20) {
    label = d.label.substring(0, 20) + '...';
  }
  if (!short && d.date) {
    label = `${d.date}: ${label}`;
  }
  return label;
}

function drag(sim) {
  return d3.drag()
    .on('start', (event, d) => {
      if (!event.active) {
        sim.alphaTarget(0.3).restart()
      }
      d.fx = d.x;
      d.fy = d.y;
    })
    .on('drag', (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    })
    .on('end', (event, d) => {
      if (!event.active) {
        sim.alphaTarget(0)
      }
      d.fx = null;
      d.fy = null;
    });
}

function renderGraph() {
  const min_weight = Math.min.apply(Math, d3_links.value.map(x => x.weight))
  const max_weight = Math.max.apply(Math, d3_links.value.map(x => x.weight))

  const strokeWidthScale = d3.scaleLinear().domain([min_weight, max_weight]).range([1, 15]).clamp(true);
  const opacityScale = d3.scaleLinear().domain([min_weight, max_weight]).range([0.5, 0.8]).clamp(true);
  const connectionScale = d3.scaleLinear().domain([1, 30]).range([8, 24]).clamp(true);
  const colorScale = d3.scaleLinear().domain([1, 10]).range([0, 359]).clamp(true); // H in HSL
  const linkLengthScale = d3.scaleLinear().domain([1, 50]).range([10, 500]).clamp(true);

  const link = linkGroup
    .selectAll('link')
    .data(d3_links.value, d => `${d.source.id}-${d.target.id}`)
    .join(
      enter => {
        const g = enter.append('g').attr('class', 'link')

        g.append('line')
          .attr('stroke', '#aaa')
          .attr('stroke-opacity', d => opacityScale(d.weight))
          .attr('stroke-width', d => strokeWidthScale(d.weight));

        g.append('text')
          .text(d => d.weight)
          .attr('fill', 'white')
          .attr('font-size', 15)
          .style('pointer-events', 'none')
          .style('visibility', 'hidden');

        g.on('mouseover', (event, d) => {
          d3.select(event.currentTarget)
            .select('text')
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2)
            .style('visibility', 'visible');
        }).on('mouseout', (event, d) => {
          d3.select(event.currentTarget)
            .select('text')
            .style('visibility', 'hidden');
        });

        return g
      },
      update => update,
      exit => exit.remove()
    );

  const node = nodeGroup
    .selectAll('g.node')
    .data(d3_nodes.value, d => d.id)
    .join(
      enter => {
        // new nodes
        const g = enter.append('g').attr('class', 'node');

        g.append('circle')
          .attr('r', d => connectionScale(getConnectionCount(d)))
          .attr('fill', d => d3.hsl(colorScale(queries.get(d.id) || 0), 0.8, 0.5))
          .attr('stroke', '#fff')
          .attr('stroke-width', 1);

        g.append('text')
          .text(d => getNodeLabel(d))
          .attr('x', 15)
          .attr('y', 5)
          .attr('fill', 'white')
          .attr('font-size', 15)
          .style('pointer-events', 'none')
          .style('opacity', 0.3);

        g.call(drag(simulation));

        g.on('mouseover', (event, d) => {
          currentPaper.value = papers.get(d.id)
          d3.select(event.currentTarget)
            .select('circle')
            .attr('r', d => connectionScale(getConnectionCount(d)) + 3);
          d3.select(event.currentTarget)
            .select('text')
            .style('opacity', 1)
            .text(d => getNodeLabel(d, false));
        }).on('mouseout', (event, d) => {
          d3.select(event.currentTarget)
            .select('circle')
            .attr('r', d => connectionScale(getConnectionCount(d)));
          d3.select(event.currentTarget)
            .select('text')
            .style('opacity', 0.3)
            .text(d => getNodeLabel(d));
        }).on('click', (event, d) => {
          loadData(d.id);
        });

        return g;
      },
      update => {
        // existing nodes
        update.select('circle')
          .transition().duration(300)
          .attr('fill', d => d3.hsl(colorScale(queries.get(d.id) || 0), 0.8, 0.5))
          .attr('r', d => connectionScale(getConnectionCount(d)));
        return update;
      },
      exit => exit.transition().duration(300)
        .style('opacity', 0)
        .remove()
    );

  simulation.nodes(d3_nodes.value);
  simulation.force('link')
    .links(d3_links.value)
    .distance(d => {
      const c1 = getConnectionCount(d.source)
      const c2 = getConnectionCount(d.target)
      return linkLengthScale(Math.min(c1, c2))
    });
  simulation.alpha(0.01).restart(); // todo
}

function ticked() {
  linkGroup.selectAll('line')
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y);

  nodeGroup.selectAll('g.node')
    .attr('transform', d => `translate(${d.x},${d.y})`);
}

function createNode(paper, refNode = null) {
  if (papers.has(paper.id)) {
    return d3_nodes.value.find(n => n.id === paper.id)
  }

  papers.set(paper.id, paper);
  const newNode = {
    id: paper.id,
    label: paper.title || `Paper ${paper.id}`,
    date: paper.update_date,
    isCenter: paper.id === initialPaperId,
    x: refNode?.x || 0,
    y: refNode?.y || 0,
    vx: 0,
    vy: 0,
  };
  d3_nodes.value.push(newNode);
  return newNode
}

function createLink(node1, node2, weight) {
  // Ensure links are always stored with the lower ID first to simplify checking
  const id1 = node1.id < node2.id ? node1.id : node2.id;
  const id2 = node1.id < node2.id ? node2.id : node1.id;
  const key = `${id1}-${id2}`;

  if (links.has(key)) {
    return
  }

  links.add(key);

  d3_links.value.push({
    source: node1,
    target: node2,
    weight: weight || 0.5
  });
}

function addResultData(results) {
  const _paper = results.paper;
  const _matches = results.matches || [];

  if (!_paper || !_paper.id) {
    console.error("Invalid paper data in results:", results);
    return;
  }

  const nodeMain = createNode(_paper);

  _matches.forEach(match => {
    const nodeOther = createNode(match._source, nodeMain);
    createLink(nodeMain, nodeOther, match._score);
  });
}

async function loadData(id) {
  statusMessage.value = "Loading data, please wait...";

  try {
    if (!queries.has(id)) {
      queries.set(id, 1)
    }

    const page = queries.get(id)
    const response = await fetch('http://localhost:3001/paper_by_id_and_knn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        paper_id: id,
        page: page,
      }),
    });

    if (!response.ok) {
      showErrorStatus('Data Loading Response NOT OK', response.status);
      return;
    }

    const result = await response.json();
    statusMessage.value = "";

    console.log('API Result:', result);
    queries.set(id, page + 1)

    addResultData(result);
    renderGraph();

  } catch (error) {
    showErrorStatus('Catched Error', error);
  }
}

onMounted(async () => {
  await nextTick(); // Wait for the DOM element to be available

  // Create SVG canvas
  const width = graphContainer.value.clientWidth;
  const height = graphContainer.value.clientHeight;
  svg = d3.select(graphContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`);

  graphContent = svg.append('g');
  linkGroup = graphContent.append('g')
    .attr('class', 'links'); // for selection, not styling
  nodeGroup = graphContent.append('g')
    .attr('class', 'nodes');

  simulation = d3.forceSimulation()
    .nodes(d3_nodes.value)
    .force('link', d3.forceLink(d3_links.value)
      .id(d => d.id)
      .distance(10)
      .strength(linkStiffness.value))
    .force('charge', d3.forceManyBody()
      .strength(linkAttraction.value))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide()
      .radius(d => (d.isCenter ? 15 : 10))
      .strength(0.8))
    .on('tick', ticked);

  const zoom = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', (event) => {
      graphContent.attr('transform', event.transform);
    });

  svg.call(zoom);

  await loadData(initialPaperId)
  currentPaper.value = papers.get(initialPaperId)

  const resizeObserver = new ResizeObserver(entries => {
    for (let entry of entries) {
      const { width, height } = entry.contentRect;
      if (svg) {
        svg.attr('viewBox', `0 0 ${width} ${height}`);
        simulation.force('center', d3.forceCenter(width / 2, height / 2))
          .alpha(0.1)
          .restart();
      }
    }
  });
  if (graphContainer.value) {
    resizeObserver.observe(graphContainer.value);
  }
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

.graph-config {
  position: absolute;
  width: 400px;
  background-color: #2d2c2c;
  border-radius: 8px;
  padding: 5px 15px;
}

.graph-config-row {
  display: flex;
  align-items: center;
}

.graph-config-row .label {
  width: 120px;
  margin-right: 10px;
}

.bg-gray {
  border: 1px solid #444;
  border-radius: 8px;
  background-color: #1d1d1d;
  height: calc(100vh - 160px);
  max-height: 100%;
}

.graph-container {
  height: 100%;
  overflow: hidden;
}

.paper-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.line-clamp {
  flex-grow: 1;
  overflow-y: auto;
}
</style>