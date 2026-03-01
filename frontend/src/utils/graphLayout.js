// Assigns x/y positions to pipeline nodes for React Flow rendering.
// Layout: top-down DAG with nodes grouped by layer.

const NODE_W = 200
const NODE_H = 70
const H_GAP = 40   // horizontal gap between siblings
const V_GAP = 80   // vertical gap between layers

function getLayer(node) {
  const id = node.id
  if (id === 'node-orchestrator') return 0
  if (id === 'node-research' || id === 'node-audience' || id === 'node-catalog') return 1
  if (id === 'node-outline') return 2
  if (id.startsWith('node-script-')) return 3
  if (id.startsWith('node-review-')) return 4
  if (id.startsWith('node-conflict-')) return 5
  return 6
}

function getModuleKey(node) {
  // Returns the module id suffix so we can group per-module nodes together
  const id = node.id
  for (const prefix of ['node-script-', 'node-review-tech-', 'node-review-ped-', 'node-review-biz-', 'node-conflict-']) {
    if (id.startsWith(prefix)) return id.slice(prefix.length)
  }
  return null
}

export function layoutNodes(nodes) {
  // Group by layer
  const layers = {}
  for (const n of nodes) {
    const l = getLayer(n)
    if (!layers[l]) layers[l] = []
    layers[l].push(n)
  }

  // For layers 3-5, sort by module key so per-module nodes stay aligned vertically
  for (const l of [3, 4, 5]) {
    if (!layers[l]) continue
    layers[l].sort((a, b) => {
      const ka = getModuleKey(a) || ''
      const kb = getModuleKey(b) || ''
      return ka.localeCompare(kb)
    })
  }

  const positioned = {}

  for (const [layerStr, layerNodes] of Object.entries(layers)) {
    const layer = parseInt(layerStr)
    const y = layer * (NODE_H + V_GAP)
    const totalW = layerNodes.length * NODE_W + (layerNodes.length - 1) * H_GAP
    const startX = -totalW / 2

    layerNodes.forEach((n, i) => {
      positioned[n.id] = {
        x: startX + i * (NODE_W + H_GAP),
        y,
      }
    })
  }

  // Build edges from dependencies
  const rfNodes = nodes.map(n => ({
    id: n.id,
    type: 'pipelineNode',
    position: positioned[n.id] || { x: 0, y: 0 },
    data: n,
  }))

  const rfEdges = []
  for (const n of nodes) {
    for (const dep of (n.dependencies || [])) {
      rfEdges.push({
        id: `${dep}->${n.id}`,
        source: dep,
        target: n.id,
        animated: n.status === 'running',
        style: { stroke: '#475569', strokeWidth: 1.5 },
      })
    }
  }

  return { rfNodes, rfEdges }
}
