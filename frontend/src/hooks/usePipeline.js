import { useCallback, useEffect, useRef, useState } from 'react'

const API = 'http://localhost:8000'

export function usePipeline() {
  const [pipelineId, setPipelineId] = useState(null)
  const [pipeline, setPipeline] = useState(null)
  const [logEntries, setLogEntries] = useState([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const logPollRef = useRef(null)

  // ── WebSocket ──────────────────────────────────────────────────────────────

  const openWebSocket = useCallback((id) => {
    if (wsRef.current) wsRef.current.close()
    const ws = new WebSocket(`ws://localhost:8000/ws/pipeline/${id}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data)

      if (msg.type === 'pipeline_state') {
        setPipeline(msg.data)

      } else if (msg.type === 'node_status_changed') {
        setPipeline(prev => {
          if (!prev) return prev
          return {
            ...prev,
            nodes: prev.nodes.map(n => {
              if (n.id !== msg.node_id) return n
              return {
                ...n,
                status: msg.status,
                ...(msg.output_data !== undefined ? { output_data: msg.output_data } : {}),
              }
            }),
          }
        })

      } else if (msg.type === 'graph_expanded') {
        setPipeline(prev => {
          if (!prev) return prev
          return { ...prev, nodes: [...prev.nodes, ...msg.new_nodes] }
        })

      } else if (msg.type === 'pipeline_completed') {
        setPipeline(prev => prev ? { ...prev, status: 'completed' } : prev)

      } else if (msg.type === 'pipeline_error') {
        setPipeline(prev => prev ? { ...prev, status: 'failed' } : prev)
        setError(msg.error)

      } else if (msg.type === 'pipeline_started') {
        setPipeline(prev => prev ? { ...prev, status: 'running' } : prev)
      }
    }
  }, [])

  // ── Log polling ────────────────────────────────────────────────────────────

  const fetchLog = useCallback(async (id) => {
    try {
      const res = await fetch(`${API}/api/log/${id}`)
      const data = await res.json()
      setLogEntries(data.entries || [])
    } catch {}
  }, [])

  useEffect(() => {
    if (!pipelineId || !pipeline) return
    fetchLog(pipelineId)
    if (pipeline.status === 'running') {
      logPollRef.current = setInterval(() => fetchLog(pipelineId), 3000)
    }
    return () => clearInterval(logPollRef.current)
  }, [pipelineId, pipeline?.status, fetchLog])

  useEffect(() => () => {
    wsRef.current?.close()
    clearInterval(logPollRef.current)
  }, [])

  // ── Actions ────────────────────────────────────────────────────────────────

  const submitBrief = useCallback(async (brief) => {
    setError(null)
    const res = await fetch(`${API}/api/brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief }),
    })
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    setPipelineId(data.pipeline_id)
    // Fetch initial pipeline state
    const pr = await fetch(`${API}/api/pipeline/${data.pipeline_id}`)
    setPipeline(await pr.json())
    return data.pipeline_id
  }, [])

  const startPipeline = useCallback(async () => {
    if (!pipelineId) return
    const res = await fetch(`${API}/api/pipeline/${pipelineId}/start`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    openWebSocket(pipelineId)
    // Refresh full state after start
    const pr = await fetch(`${API}/api/pipeline/${pipelineId}`)
    setPipeline(await pr.json())
  }, [pipelineId, openWebSocket])

  const refreshNode = useCallback(async (nodeId) => {
    if (!pipelineId) return
    const res = await fetch(`${API}/api/node/${nodeId}?pipeline_id=${pipelineId}`)
    const updated = await res.json()
    setPipeline(prev => {
      if (!prev) return prev
      return { ...prev, nodes: prev.nodes.map(n => n.id === nodeId ? updated : n) }
    })
  }, [pipelineId])

  const approveNode = useCallback(async (nodeId) => {
    await fetch(`${API}/api/node/${nodeId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pipeline_id: pipelineId }),
    })
    await refreshNode(nodeId)
  }, [pipelineId, refreshNode])

  const editNode = useCallback(async (nodeId, editedOutput) => {
    await fetch(`${API}/api/node/${nodeId}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pipeline_id: pipelineId, edited_output: editedOutput }),
    })
    await refreshNode(nodeId)
  }, [pipelineId, refreshNode])

  const decideNode = useCallback(async (nodeId, decisionOrDecisions) => {
    const body = { pipeline_id: pipelineId }
    if (typeof decisionOrDecisions === 'object' && decisionOrDecisions !== null) {
      body.decisions = decisionOrDecisions
    } else {
      body.decision = decisionOrDecisions
    }
    await fetch(`${API}/api/node/${nodeId}/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    await refreshNode(nodeId)
  }, [pipelineId, refreshNode])

  const sendChat = useCallback(async (nodeId, message) => {
    const res = await fetch(`${API}/api/chat/${nodeId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pipeline_id: pipelineId, message }),
    })
    return res.json()
  }, [pipelineId])

  return {
    pipelineId, pipeline, logEntries, connected, error,
    submitBrief, startPipeline, approveNode, editNode, decideNode, sendChat,
  }
}
