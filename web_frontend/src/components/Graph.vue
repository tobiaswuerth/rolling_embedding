<template>
  <v-container class="py-8" fluid>
    <v-responsive class="mx-auto" max-width="100%">
      <a href="/">
        <v-img class="mb-4" height="150" src="@/assets/logo.png" />
      </a>

      <div class="text-center mb-6">
        <h1 class="text-h2 font-weight-bold">Graph</h1>
      </div>

      <div ref="graphContainer" class="graph-container"></div>
    </v-responsive>
  </v-container>
</template>

<script setup>
import * as d3 from 'd3'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const paper_id = route.params.id
const graphContainer = ref(null)

const paper = ref({})
const matches = ref([])

async function loadData() {
  const response = await fetch('http://localhost:3001/search_by_paper_id', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      paper_id: paper_id,
    }),
  })

  if (!response.ok) {
    console.error('Error fetching data:', response.statusText)
    return
  }

  const result = await response.json()
  paper.value = result['paper']
  matches.value = result['matches']
  console.log(matches.value)

  generateGraph()
}

function generateGraph() {
  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight

  // Prepare nodes and links
  console.log(paper.value)
  const nodes = [
    {
      id: paper_id,
      label: paper.value.title,
      isCenter: true
    },
    ...matches.value.map(result => ({
      id: result._id,
      label: `${result._score.toFixed(3)}: ${result._source.title}`,
      isCenter: false,
    }))
  ]

  const links = matches.value.map(result => ({
    source: paper_id,
    target: result._id,
    weight: result._score,
  }))

  // Create the SVG container
  const svg = d3.select(graphContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .style('background-color', '#1d1d1d');

  // Create the force simulation
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2));

  // Draw links (edges)
  const link = svg.append('g')
    .attr('stroke', '#aaa')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke-width', d => Math.max(d.weight * 2, 1));

  // Create a group for each node (to include both circle and label)
  const nodeGroup = svg.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g');

  // Draw nodes (circles) inside the group
  const node = nodeGroup
    .append('circle')
    .attr('r', 10)
    .attr('fill', d => d.isCenter ? '#1976d2' : '#00bcd4')  // Center node in blue, others in teal
    .call(drag(simulation));

  // Add labels (text) inside each node group, initially hidden
  const label = nodeGroup
    .append('text')
    .text(d => d.label)
    .attr('font-size', 12)
    .attr('dx', 12)
    .attr('dy', 4)
    .attr('fill', 'white')
    .style('opacity', 0.3);

  // Show the label on hover
  node.on('mouseover', (event, d) => {
    d3.select(event.target.parentNode)
      .select('text')
      .style('opacity', 1);
  }).on('mouseout', (event, d) => {
    d3.select(event.target.parentNode)
      .select('text')
      .style('opacity', 0.3);
  });

  // Update the graph's position on simulation tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y);

    label
      .attr('x', d => d.x)
      .attr('y', d => d.y);
  });

  // Drag functionality
  function drag(sim) {
    return d3.drag()
      .on('start', event => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', event => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on('end', event => {
        if (!event.active) sim.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      });
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.graph-container {
  height: 400px;
}

svg {
  width: 100%;
  height: 100%;
  border-radius: 8px;
}
</style>
