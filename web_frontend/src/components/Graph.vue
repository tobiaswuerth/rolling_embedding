<template>
  <v-container class="py-8" fluid>
    <v-responsive class="mx-auto" max-width="100%">
      <a href="/">
        <v-img class="mb-4" height="150" src="@/assets/logo.png" />
      </a>

      <div class="text-center mb-6">
        <h1 class="text-h2 font-weight-bold">Graph</h1>
        <p v-if="currentPaperId" class="text-subtitle-1">Displaying connections for Paper ID: {{ currentPaperId }}</p>
      </div>

      <div ref="graphContainer" class="graph-container"></div>
      <p v-if="isLoading" class="text-center mt-4">Loading graph data...</p>
      <p v-if="errorLoading" class="text-center mt-4 red--text">Error loading graph data.</p>
    </v-responsive>
  </v-container>
</template>

<script setup>
import * as d3 from 'd3';
import { onMounted, ref, nextTick } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const initialPaperId = route.params.id;

const currentPaperId = ref(null);
const isLoading = ref(false);
const errorLoading = ref(false);

const graphContainer = ref(null);
let simulation = null;
const papers = new Map();
const links = new Set();
const d3_nodes = ref([]);
const d3_links = ref([]);
let svg = null;
let linkGroup = null;
let nodeGroup = null;


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
  const link = linkGroup
    .selectAll('line')
    .data(d3_links.value, d => `${d.source.id}-${d.target.id}`)
    .join(
      enter => enter.append('line')
        .attr('stroke', '#aaa')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.weight * 5)),
      update => update,
      exit => exit.remove()
    );

  const node = nodeGroup
    .selectAll('g.node')
    .data(d3_nodes.value, d => d.id)
    .join(
      enter => {
        const g = enter.append('g').attr('class', 'node');

        g.append('circle')
          .attr('r', d => d.isCenter ? 12 : 8)
          .attr('fill', d => d.isCenter ? '#1976d2' : '#00bcd4')
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5);

        g.append('text')
          .text(d => d.label.length > 20 ? d.label.substring(0, 20) + '...' : d.label)
          .attr('x', 15)
          .attr('y', 4)
          .attr('fill', 'white')
          .attr('font-size', 15)
          .style('pointer-events', 'none')
          .style('opacity', 0.3);

        g.call(drag(simulation));

        g.on('mouseover', (event, d) => {
          d3.select(event.currentTarget)
            .select('circle')
            .attr('r', d.isCenter ? 14 : 10);
          d3.select(event.currentTarget)
            .select('text')
            .style('opacity', 1)
            .text(d.label);
        }).on('mouseout', (event, d) => {
          d3.select(event.currentTarget)
            .select('circle')
            .attr('r', d.isCenter ? 12 : 8);
          d3.select(event.currentTarget)
            .select('text')
            .style('opacity', 0.3)
            .text(d => d.label.length > 20 ? d.label.substring(0, 20) + '...' : d.label);
        });

        g.on('click', async (event, d) => {
          // Prevent triggering click during drag
          if (event.defaultPrevented) {
            return
          };

          loadData(d.id)
        });

        return g;
      },
      update => {
        update.select('circle')
          .transition().duration(300)
          .attr('fill', d => d.isCenter ? '#1976d2' : '#00bcd4')
          .attr('r', d => d.isCenter ? 12 : 8);
        update.select('text')
          .text(d => d.label.length > 20 ? d.label.substring(0, 20) + '...' : d.label);
        return update;
      },
      exit => exit.transition().duration(300)
        .style('opacity', 0)
        .remove()
    );

  simulation.nodes(d3_nodes.value);
  simulation.force('link').links(d3_links.value);
  simulation.alpha(1).restart();
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

function createNode(paper) {
  if (papers.has(paper.id)) {
    return d3_nodes.value.find(n => n.id === paper.id)
  }

  papers.set(paper.id, paper);
  const newNode = {
    id: paper.id,
    label: paper.title || `Paper ${paper.id}`,
    isCenter: paper.id === initialPaperId,
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
    const nodeOther = createNode(match._source);
    createLink(nodeMain, nodeOther, match._score);
  });
}

async function loadData(id) {
  if (isLoading.value) {
    // Prevent concurrent loads
    return
  }

  isLoading.value = true;
  errorLoading.value = false;

  try {
    const response = await fetch('http://localhost:3001/search_by_paper_id', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paper_id: id }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('API Result:', result);

    addResultData(result);
    renderGraph();

  } catch (error) {
    console.error('Error fetching or processing data:', error);
    errorLoading.value = true;
  } finally {
    isLoading.value = false;
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
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('background-color', '#1d1d1d');

  linkGroup = svg.append('g').attr('class', 'links'); // for selection, not styling
  nodeGroup = svg.append('g').attr('class', 'nodes');

  simulation = d3.forceSimulation()
    .nodes(d3_nodes.value)
    .force('link', d3.forceLink(d3_links.value).id(d => d.id).distance(80).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-250))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collide', d3.forceCollide().radius(d => (d.isCenter ? 15 : 10)).strength(0.7))
    .on('tick', ticked);

  await loadData(initialPaperId)

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
.graph-container {
  height: 600px;
  width: 100%;
  border: 1px solid #444;
  border-radius: 8px;
}
</style>