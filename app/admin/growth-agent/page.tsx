'use client'

/**
 * app/admin/growth-agent/page.tsx
 *
 * The Growth Agent admin review interface.
 * Bloomberg Terminal meets editorial desk.
 * Human reviews every draft before it publishes.
 *
 * Features:
 * - Queue view filtered by status / type / vertical
 * - Inline edit before approve
 * - One-click approve / reject
 * - Run agent manually
 * - Live stats bar
 */

import { useState, useEffect, useCallback } from 'react'

// ─── Types ────────────────────────────────────────────────────

type OutputType =
  | 'social_x'
  | 'social_linkedin'
  | 'social_discord'
  | 'geo_block'
  | 'index_post'
  | 'signal_page'
  | 'comparison_page'
  | 'template_geo'

type Status = 'draft' | 'approved' | 'rejected' | 'published'

interface QueueItem {
  id: number
  output_type: OutputType
  title: string
  content: string
  target_url: string | null
  meta_description: string | null
  signal_ids: number[]
  tool_slug: string | null
  vertical: string | null
  briefing_date: string
  status: Status
  review_notes: string | null
  rejection_reason: string | null
  approved_by_email: string | null
  published_at: string | null
  scheduled_for: string | null
  created_at: string
}

interface AgentRun {
  id: number
  run_type: string
  status: string
  signals_processed: number
  outputs_generated: number
  started_at: string
  completed_at: string | null
  duration_ms: number | null
}

// ─── Constants ────────────────────────────────────────────────

const TYPE_LABELS: Record<OutputType, string> = {
  social_x: 'X Post',
  social_linkedin: 'LinkedIn',
  social_discord: 'Discord',
  geo_block: 'GEO Block',
  index_post: 'Index Post',
  signal_page: 'Signal Page',
  comparison_page: 'Comparison',
  template_geo: 'Template GEO',
}

const TYPE_COLORS: Record<OutputType, string> = {
  social_x: '#c8f04a',
  social_linkedin: '#4a90e2',
  social_discord: '#5865f2',
  geo_block: '#f0a83c',
  index_post: '#e87060',
  signal_page: '#b07af0',
  comparison_page: '#3cc8a0',
  template_geo: '#f0a83c',
}

const VERTICAL_LABELS: Record<string, string> = {
  product_photography: 'Product Photo',
  filmmaking: 'Film',
  digital_humans: 'Digital Humans',
}

// ─── Component ────────────────────────────────────────────────

export default function GrowthAgentAdmin() {
  const [items, setItems] = useState<QueueItem[]>([])
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState<Status>('draft')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<QueueItem | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [agentRunning, setAgentRunning] = useState(false)
  const [lastRun, setLastRun] = useState<AgentRun | null>(null)
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [toast, setToast] = useState<{ msg: string; type: 'ok' | 'err' } | null>(null)

  const showToast = (msg: string, type: 'ok' | 'err' = 'ok') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const fetchQueue = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ status: statusFilter, limit: '30' })
      if (typeFilter) params.set('type', typeFilter)
      const res = await fetch(`/api/agent/queue?${params}`)
      const data = await res.json()
      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch {
      showToast('Failed to load queue', 'err')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, typeFilter])

  const fetchCounts = async () => {
    const statuses: Status[] = ['draft', 'approved', 'rejected', 'published']
    const results: Record<string, number> = {}
    await Promise.all(
      statuses.map(async (s) => {
        const res = await fetch(`/api/agent/queue?status=${s}&limit=1`)
        const data = await res.json()
        results[s] = data.total || 0
      })
    )
    setCounts(results)
  }

  useEffect(() => { fetchQueue() }, [fetchQueue])
  useEffect(() => { fetchCounts() }, [])

  const selectItem = (item: QueueItem) => {
    setSelectedItem(item)
    setEditContent(formatContent(item))
    setEditNotes(item.review_notes || '')
    setRejectionReason('')
  }

  const formatContent = (item: QueueItem): string => {
    try {
      const parsed = JSON.parse(item.content)
      return JSON.stringify(parsed, null, 2)
    } catch {
      return item.content
    }
  }

  const action = async (act: 'approve' | 'reject' | 'edit') => {
    if (!selectedItem) return
    const payload: Record<string, unknown> = {
      id: selectedItem.id,
      action: act,
      review_notes: editNotes,
    }
    if (act === 'approve' || act === 'edit') {
      try { payload.content = JSON.stringify(JSON.parse(editContent)) }
      catch { payload.content = editContent }
    }
    if (act === 'reject') payload.rejection_reason = rejectionReason

    const res = await fetch('/api/agent/queue', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (res.ok) {
      const label = act === 'approve' ? 'Approved' : act === 'reject' ? 'Rejected' : 'Saved'
      showToast(`${label}: ${selectedItem.title}`)
      setSelectedItem(null)
      fetchQueue()
      fetchCounts()
    } else {
      showToast('Action failed', 'err')
    }
  }

  const runAgent = async (runType = 'on_demand') => {
    setAgentRunning(true)
    try {
      const res = await fetch('/api/cron/growth-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ runType }),
      })
      const data = await res.json()
      if (data.success) {
        showToast(`Agent complete — ${data.outputs} outputs queued`)
        fetchQueue()
        fetchCounts()
      } else {
        showToast(`Agent failed: ${data.error}`, 'err')
      }
    } catch {
      showToast('Agent request failed', 'err')
    } finally {
      setAgentRunning(false)
    }
  }

  // ─── Render ─────────────────────────────────────────────────

  return (
    <div style={styles.root}>
      {/* Toast */}
      {toast && (
        <div style={{ ...styles.toast, background: toast.type === 'ok' ? '#c8f04a' : '#e87060', color: '#0e0e0e' }}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}>GENLENS</span>
          <span style={styles.headerSep}>／</span>
          <span style={styles.headerTitle}>Growth Agent</span>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.countPills}>
            {Object.entries(counts).map(([s, n]) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s as Status)}
                style={{
                  ...styles.countPill,
                  borderColor: statusFilter === s ? '#c8f04a' : 'rgba(255,255,255,0.1)',
                  color: statusFilter === s ? '#c8f04a' : 'rgba(255,255,255,0.4)',
                }}
              >
                <span style={{ color: statusFilter === s ? '#c8f04a' : 'rgba(255,255,255,0.6)', fontWeight: 500 }}>{n}</span>
                {' '}{s}
              </button>
            ))}
          </div>
          <button
            onClick={() => runAgent('on_demand')}
            disabled={agentRunning}
            style={styles.runBtn}
          >
            {agentRunning ? '▸ running...' : '▸ run agent'}
          </button>
          <button onClick={() => runAgent('weekly_index')} disabled={agentRunning} style={styles.runBtnSecondary}>
            ▸ index run
          </button>
        </div>
      </div>

      {/* Type filter tabs */}
      <div style={styles.typeTabs}>
        <button onClick={() => setTypeFilter('')} style={{ ...styles.typeTab, ...(typeFilter === '' ? styles.typeTabActive : {}) }}>
          All
        </button>
        {Object.entries(TYPE_LABELS).map(([type, label]) => (
          <button
            key={type}
            onClick={() => setTypeFilter(type === typeFilter ? '' : type)}
            style={{
              ...styles.typeTab,
              ...(typeFilter === type ? {
                borderColor: TYPE_COLORS[type as OutputType],
                color: TYPE_COLORS[type as OutputType],
              } : {}),
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Main split layout */}
      <div style={styles.main}>
        {/* Queue list */}
        <div style={styles.list}>
          {loading && <div style={styles.loadingRow}>loading queue…</div>}
          {!loading && items.length === 0 && (
            <div style={styles.emptyRow}>
              No {statusFilter} items{typeFilter ? ` of type ${TYPE_LABELS[typeFilter as OutputType]}` : ''}.
              {statusFilter === 'draft' && (
                <button onClick={() => runAgent()} style={styles.inlineRunBtn}>Run agent →</button>
              )}
            </div>
          )}
          {items.map(item => (
            <div
              key={item.id}
              onClick={() => selectItem(item)}
              style={{
                ...styles.listItem,
                ...(selectedItem?.id === item.id ? styles.listItemActive : {}),
              }}
            >
              <div style={styles.listItemTop}>
                <span
                  style={{
                    ...styles.typeBadge,
                    color: TYPE_COLORS[item.output_type],
                    borderColor: TYPE_COLORS[item.output_type] + '44',
                    background: TYPE_COLORS[item.output_type] + '11',
                  }}
                >
                  {TYPE_LABELS[item.output_type]}
                </span>
                {item.vertical && (
                  <span style={styles.verticalBadge}>
                    {VERTICAL_LABELS[item.vertical] ?? item.vertical}
                  </span>
                )}
                <span style={styles.itemDate}>
                  {new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
              </div>
              <div style={styles.listItemTitle}>{item.title}</div>
              {item.target_url && (
                <div style={styles.listItemUrl}>{item.target_url}</div>
              )}
              {item.scheduled_for && (
                <div style={styles.scheduledBadge}>
                  ⏰ {new Date(item.scheduled_for).toLocaleString('en-US', {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                  })}
                </div>
              )}
            </div>
          ))}
          {total > items.length && (
            <div style={styles.moreRow}>+{total - items.length} more items</div>
          )}
        </div>

        {/* Detail / editor */}
        <div style={styles.detail}>
          {!selectedItem ? (
            <div style={styles.detailEmpty}>
              <div style={styles.detailEmptyIcon}>▸</div>
              <div style={styles.detailEmptyText}>Select an item to review</div>
            </div>
          ) : (
            <>
              {/* Detail header */}
              <div style={styles.detailHeader}>
                <div>
                  <span style={{
                    ...styles.typeBadge,
                    color: TYPE_COLORS[selectedItem.output_type],
                    borderColor: TYPE_COLORS[selectedItem.output_type] + '55',
                    background: TYPE_COLORS[selectedItem.output_type] + '15',
                    marginRight: 8,
                  }}>
                    {TYPE_LABELS[selectedItem.output_type]}
                  </span>
                  <span style={styles.detailTitle}>{selectedItem.title}</span>
                </div>
                <div style={styles.detailMeta}>
                  {selectedItem.target_url && (
                    <span style={styles.detailUrl}>{selectedItem.target_url}</span>
                  )}
                  {selectedItem.signal_ids?.length > 0 && (
                    <span style={styles.detailMuted}>
                      {selectedItem.signal_ids.length} signal{selectedItem.signal_ids.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              </div>

              {/* Content editor */}
              <div style={styles.editorSection}>
                <div style={styles.editorLabel}>Content</div>
                <textarea
                  value={editContent}
                  onChange={e => setEditContent(e.target.value)}
                  style={styles.editor}
                  rows={selectedItem.output_type === 'social_x' ? 4 : 16}
                  spellCheck={false}
                />
                {selectedItem.output_type === 'social_x' && (
                  <div style={{
                    ...styles.charCount,
                    color: editContent.length > 280 ? '#e87060' : 'rgba(255,255,255,0.3)',
                  }}>
                    {editContent.length} / 280 chars
                  </div>
                )}
              </div>

              {/* Meta description (if GEO type) */}
              {selectedItem.meta_description && (
                <div style={styles.editorSection}>
                  <div style={styles.editorLabel}>Meta description</div>
                  <div style={styles.metaDesc}>{selectedItem.meta_description}</div>
                </div>
              )}

              {/* Target URL */}
              {selectedItem.target_url && (
                <div style={styles.editorSection}>
                  <div style={styles.editorLabel}>Publishes to</div>
                  <div style={styles.urlDisplay}>{selectedItem.target_url}</div>
                </div>
              )}

              {/* Review notes */}
              <div style={styles.editorSection}>
                <div style={styles.editorLabel}>Review notes (optional)</div>
                <textarea
                  value={editNotes}
                  onChange={e => setEditNotes(e.target.value)}
                  style={{ ...styles.editor, height: 60 }}
                  placeholder="Notes for the record..."
                />
              </div>

              {/* Actions */}
              {selectedItem.status === 'draft' && (
                <div style={styles.actions}>
                  <button onClick={() => action('approve')} style={styles.approveBtn}>
                    ✓ Approve
                  </button>
                  <button onClick={() => action('edit')} style={styles.editBtn}>
                    Save edits
                  </button>
                  <div style={styles.rejectSection}>
                    <input
                      value={rejectionReason}
                      onChange={e => setRejectionReason(e.target.value)}
                      placeholder="Rejection reason..."
                      style={styles.rejectInput}
                    />
                    <button
                      onClick={() => action('reject')}
                      disabled={!rejectionReason}
                      style={styles.rejectBtn}
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>
              )}

              {selectedItem.status === 'approved' && (
                <div style={styles.statusBar}>
                  <span style={{ color: '#c8f04a' }}>✓ Approved</span>
                  {selectedItem.approved_by_email && (
                    <span style={styles.detailMuted}>by {selectedItem.approved_by_email}</span>
                  )}
                  {selectedItem.scheduled_for && (
                    <span style={styles.detailMuted}>
                      publishes {new Date(selectedItem.scheduled_for).toLocaleString()}
                    </span>
                  )}
                </div>
              )}

              {selectedItem.status === 'published' && (
                <div style={styles.statusBar}>
                  <span style={{ color: '#3cc8a0' }}>✓ Published</span>
                  {selectedItem.published_at && (
                    <span style={styles.detailMuted}>
                      {new Date(selectedItem.published_at).toLocaleString()}
                    </span>
                  )}
                </div>
              )}

              {selectedItem.status === 'rejected' && (
                <div style={styles.statusBar}>
                  <span style={{ color: '#e87060' }}>✕ Rejected</span>
                  {selectedItem.rejection_reason && (
                    <span style={styles.detailMuted}>{selectedItem.rejection_reason}</span>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Styles ───────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  root: {
    minHeight: '100vh',
    background: '#0e0e0e',
    color: 'rgba(255,255,255,0.85)',
    fontFamily: '"IBM Plex Mono", "Courier New", monospace',
    fontSize: 12,
    display: 'flex',
    flexDirection: 'column',
  },
  toast: {
    position: 'fixed',
    bottom: 24,
    right: 24,
    padding: '10px 20px',
    borderRadius: 4,
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 12,
    fontWeight: 500,
    zIndex: 9999,
    letterSpacing: '0.04em',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    borderBottom: '0.5px solid rgba(255,255,255,0.08)',
    background: '#0e0e0e',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: 10 },
  logo: { color: '#c8f04a', fontWeight: 700, letterSpacing: '0.12em', fontSize: 13 },
  headerSep: { color: 'rgba(255,255,255,0.2)' },
  headerTitle: { color: 'rgba(255,255,255,0.6)', letterSpacing: '0.06em' },
  headerRight: { display: 'flex', alignItems: 'center', gap: 8 },
  countPills: { display: 'flex', gap: 4 },
  countPill: {
    padding: '4px 10px',
    border: '0.5px solid',
    borderRadius: 3,
    background: 'transparent',
    cursor: 'pointer',
    fontSize: 11,
    letterSpacing: '0.05em',
    fontFamily: '"IBM Plex Mono", monospace',
    transition: 'all 0.15s',
  },
  runBtn: {
    padding: '6px 16px',
    background: '#c8f04a',
    color: '#0e0e0e',
    border: 'none',
    borderRadius: 3,
    cursor: 'pointer',
    fontWeight: 700,
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 11,
    letterSpacing: '0.06em',
  },
  runBtnSecondary: {
    padding: '6px 12px',
    background: 'transparent',
    color: 'rgba(255,255,255,0.5)',
    border: '0.5px solid rgba(255,255,255,0.15)',
    borderRadius: 3,
    cursor: 'pointer',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 11,
  },
  typeTabs: {
    display: 'flex',
    gap: 4,
    padding: '8px 20px',
    borderBottom: '0.5px solid rgba(255,255,255,0.06)',
    overflowX: 'auto',
    background: '#0a0a0a',
  },
  typeTab: {
    padding: '4px 12px',
    background: 'transparent',
    border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: 3,
    cursor: 'pointer',
    color: 'rgba(255,255,255,0.4)',
    fontSize: 11,
    fontFamily: '"IBM Plex Mono", monospace',
    whiteSpace: 'nowrap',
    transition: 'all 0.1s',
  },
  typeTabActive: { borderColor: '#c8f04a', color: '#c8f04a' },
  main: { display: 'flex', flex: 1, overflow: 'hidden', height: 'calc(100vh - 88px)' },
  list: {
    width: 320,
    flexShrink: 0,
    borderRight: '0.5px solid rgba(255,255,255,0.07)',
    overflowY: 'auto',
    padding: '8px 0',
  },
  listItem: {
    padding: '12px 16px',
    borderBottom: '0.5px solid rgba(255,255,255,0.05)',
    cursor: 'pointer',
    transition: 'background 0.1s',
  },
  listItemActive: { background: 'rgba(200,240,74,0.05)', borderLeft: '2px solid #c8f04a' },
  listItemTop: { display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, flexWrap: 'wrap' },
  typeBadge: {
    fontSize: 9,
    letterSpacing: '0.08em',
    padding: '2px 6px',
    borderRadius: 2,
    border: '0.5px solid',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  verticalBadge: {
    fontSize: 9,
    color: 'rgba(255,255,255,0.3)',
    letterSpacing: '0.05em',
  },
  itemDate: { fontSize: 9, color: 'rgba(255,255,255,0.25)', marginLeft: 'auto' },
  listItemTitle: { fontSize: 11, lineHeight: 1.5, color: 'rgba(255,255,255,0.8)', marginBottom: 3 },
  listItemUrl: { fontSize: 9, color: 'rgba(255,255,255,0.25)', fontStyle: 'italic' },
  scheduledBadge: { fontSize: 9, color: '#f0a83c', marginTop: 4 },
  loadingRow: { padding: '20px 16px', color: 'rgba(255,255,255,0.3)', textAlign: 'center' },
  emptyRow: {
    padding: '40px 16px',
    color: 'rgba(255,255,255,0.25)',
    textAlign: 'center',
    lineHeight: 2,
  },
  moreRow: { padding: '8px 16px', color: 'rgba(255,255,255,0.2)', textAlign: 'center', fontSize: 10 },
  inlineRunBtn: {
    display: 'block',
    margin: '8px auto 0',
    padding: '4px 12px',
    background: 'transparent',
    border: '0.5px solid rgba(200,240,74,0.4)',
    color: '#c8f04a',
    borderRadius: 3,
    cursor: 'pointer',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 10,
  },
  detail: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px 24px',
    display: 'flex',
    flexDirection: 'column',
    gap: 0,
  },
  detailEmpty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: 12,
    color: 'rgba(255,255,255,0.15)',
  },
  detailEmptyIcon: { fontSize: 32, color: 'rgba(255,255,255,0.1)' },
  detailEmptyText: { fontSize: 12, letterSpacing: '0.08em' },
  detailHeader: {
    paddingBottom: 16,
    borderBottom: '0.5px solid rgba(255,255,255,0.08)',
    marginBottom: 20,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  detailTitle: { fontSize: 13, color: 'rgba(255,255,255,0.9)', fontWeight: 500 },
  detailMeta: { display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' },
  detailUrl: { fontSize: 10, color: '#4a90e2', fontStyle: 'italic' },
  detailMuted: { fontSize: 10, color: 'rgba(255,255,255,0.3)' },
  editorSection: { marginBottom: 16 },
  editorLabel: {
    fontSize: 9,
    letterSpacing: '0.1em',
    color: 'rgba(255,255,255,0.3)',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  editor: {
    width: '100%',
    background: '#111',
    border: '0.5px solid rgba(255,255,255,0.1)',
    borderRadius: 4,
    color: 'rgba(255,255,255,0.8)',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 11,
    padding: '10px 12px',
    lineHeight: 1.6,
    resize: 'vertical',
    outline: 'none',
  },
  charCount: { fontSize: 10, textAlign: 'right', marginTop: 4 },
  metaDesc: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
    lineHeight: 1.6,
    padding: '8px 0',
    borderLeft: '2px solid rgba(255,255,255,0.08)',
    paddingLeft: 10,
  },
  urlDisplay: {
    fontSize: 11,
    color: '#4a90e2',
    padding: '6px 0',
    fontStyle: 'italic',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
    marginTop: 8,
    paddingTop: 16,
    borderTop: '0.5px solid rgba(255,255,255,0.08)',
  },
  approveBtn: {
    padding: '8px 20px',
    background: '#c8f04a',
    color: '#0e0e0e',
    border: 'none',
    borderRadius: 3,
    cursor: 'pointer',
    fontWeight: 700,
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 12,
    letterSpacing: '0.04em',
  },
  editBtn: {
    padding: '8px 16px',
    background: 'transparent',
    color: 'rgba(255,255,255,0.6)',
    border: '0.5px solid rgba(255,255,255,0.2)',
    borderRadius: 3,
    cursor: 'pointer',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 12,
  },
  rejectSection: { display: 'flex', gap: 6, marginLeft: 'auto', alignItems: 'center' },
  rejectInput: {
    padding: '6px 10px',
    background: '#111',
    border: '0.5px solid rgba(232,112,96,0.3)',
    borderRadius: 3,
    color: 'rgba(255,255,255,0.6)',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 11,
    width: 200,
    outline: 'none',
  },
  rejectBtn: {
    padding: '6px 14px',
    background: 'transparent',
    color: '#e87060',
    border: '0.5px solid rgba(232,112,96,0.4)',
    borderRadius: 3,
    cursor: 'pointer',
    fontFamily: '"IBM Plex Mono", monospace',
    fontSize: 11,
  },
  statusBar: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
    padding: '10px 0',
    marginTop: 8,
    borderTop: '0.5px solid rgba(255,255,255,0.08)',
  },
}
