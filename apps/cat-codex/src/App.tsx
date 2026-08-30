import { useMemo, useState } from 'react'
import { CodexAppServerClient } from './lib/codex/client'
import { UnavailableTransport } from './lib/codex/transport'
import { providers } from './lib/providers'
import { extensionLabels, installedPlugins, type PluginExtension } from './lib/plugins'

type EventKind = 'thought' | 'tool' | 'file' | 'notice'
type AgentEvent = { time: string; kind: EventKind; title: string; detail: string; tone?: 'active' | 'muted' }
type AppView = 'workspace' | 'settings'
type SettingsSection = 'general' | 'appearance' | 'models' | 'voice' | 'shortcuts' | 'permissions' | 'usage' | 'account' | 'computer' | 'history' | 'snapshots' | 'plugins' | 'browser'

const initialEvents: AgentEvent[] = [
  { time: '09:41:18', kind: 'thought', title: 'Agent is waiting', detail: 'Connect Codex App Server to start a turn.', tone: 'active' },
  { time: '09:40:52', kind: 'file', title: 'Workspace indexed', detail: '14 files · 2 directories · local only', tone: 'muted' },
  { time: '09:40:48', kind: 'notice', title: 'Permission profile', detail: 'Ask before changes · network off', tone: 'muted' },
]

const sessions = [
  { name: 'Cat Codex first pass', subtitle: 'New project', time: '09:41', selected: true },
  { name: 'LaunchMath release notes', subtitle: 'apps/LaunchMath', time: 'Yesterday' },
  { name: 'Source scan dashboard', subtitle: 'xinyuan_scan', time: 'Aug 28' },
]

const settingsSections: Array<{ id: SettingsSection; label: string; group: string }> = [
  { id: 'general', label: 'General', group: 'Workspace' },
  { id: 'appearance', label: 'Appearance', group: 'Workspace' },
  { id: 'models', label: 'Models & providers', group: 'Workspace' },
  { id: 'voice', label: 'Voice', group: 'Workspace' },
  { id: 'shortcuts', label: 'Keyboard shortcuts', group: 'Workspace' },
  { id: 'permissions', label: 'Permissions', group: 'Safety' },
  { id: 'usage', label: 'Usage & billing', group: 'Account' },
  { id: 'account', label: 'Account', group: 'Account' },
  { id: 'computer', label: 'Computer control', group: 'Tools' },
  { id: 'history', label: 'History', group: 'Tools' },
  { id: 'snapshots', label: 'App snapshots', group: 'Tools' },
  { id: 'plugins', label: 'Plugins', group: 'Tools' },
  { id: 'browser', label: 'Browser', group: 'Tools' },
]

const settingsMeta: Record<SettingsSection, { eyebrow: string; title: string; description: string; rows: Array<{ label: string; detail: string; value: string }> }> = {
  general: {
    eyebrow: 'WORKSPACE', title: 'General', description: 'Set the defaults that shape each Cat Codex workspace.',
    rows: [
      { label: 'Language', detail: 'Interface and assistant response language', value: '简体中文 · ready to apply' },
      { label: 'App Server', detail: 'Connection used for sessions and streamed events', value: 'Not connected' },
      { label: 'Startup', detail: 'Open the last workspace when the app launches', value: 'Off' },
    ],
  },
  appearance: {
    eyebrow: 'WORKSPACE', title: 'Appearance', description: 'Keep the high-density Codex layout comfortable across desktop sizes.',
    rows: [
      { label: 'Theme', detail: 'Color scheme for the workbench', value: 'Dark' },
      { label: 'Accent', detail: 'Brand signal used for active states', value: 'Cat lime' },
      { label: 'Layout density', detail: 'Spacing used by lists and event rows', value: 'Compact' },
    ],
  },
  models: {
    eyebrow: 'PROVIDERS', title: 'Models & providers', description: 'Choose a default model and connect additional providers when their adapters are installed.',
    rows: [
      { label: 'Default model', detail: 'Used for new sessions', value: 'gpt-5.6-terra' },
      { label: 'Active provider', detail: 'Provider adapter for the default model', value: 'OpenAI / Codex' },
      { label: 'Other providers', detail: 'DeepSeek, Claude, Gemini, local and compatible APIs', value: 'Not connected' },
    ],
  },
  voice: {
    eyebrow: 'INPUT', title: 'Voice', description: 'Voice controls will be enabled by the native shell when a microphone and realtime transport are configured.',
    rows: [
      { label: 'Voice input', detail: 'Microphone capture for a turn', value: 'Not configured' },
      { label: 'Spoken language', detail: 'Recognition language for voice input', value: '简体中文' },
      { label: 'Realtime transport', detail: 'Streaming channel for voice sessions', value: 'Unavailable' },
    ],
  },
  shortcuts: {
    eyebrow: 'INPUT', title: 'Keyboard shortcuts', description: 'Shortcuts stay visible in context so the workbench remains keyboard-friendly.',
    rows: [
      { label: 'Open settings', detail: 'Open this page from any workspace', value: '⌘ ,' },
      { label: 'Send message', detail: 'Submit the current composer', value: '⌘ ↵' },
      { label: 'Toggle panels', detail: 'Show or hide inspector panels', value: '⌘ \\' },
    ],
  },
  permissions: {
    eyebrow: 'SAFETY', title: 'Permissions', description: 'Review the boundary before Cat Codex can change files, run commands, or use the network.',
    rows: [
      { label: 'File changes', detail: 'Approval required before edits', value: 'Ask before changes' },
      { label: 'Network access', detail: 'Outbound requests from the native shell', value: 'Off' },
      { label: 'App Server', detail: 'Native transport endpoint', value: 'Not connected' },
    ],
  },
  usage: {
    eyebrow: 'ACCOUNT', title: 'Usage & billing', description: 'Usage reporting becomes available after an account or provider connection is configured.',
    rows: [
      { label: 'Current workspace', detail: 'Local events recorded in this session', value: 'No usage data yet' },
      { label: 'Provider billing', detail: 'Billing is handled by the selected provider', value: 'Not connected' },
      { label: 'Cost controls', detail: 'Limit or warn on provider spend', value: 'Unavailable' },
    ],
  },
  account: {
    eyebrow: 'ACCOUNT', title: 'Account', description: 'Cat Codex keeps account state outside the UI until an authenticated provider is selected.',
    rows: [
      { label: 'Signed-in account', detail: 'Identity used by the active provider', value: 'Not connected' },
      { label: 'Workspace sync', detail: 'Sync settings and sessions across devices', value: 'Off' },
    ],
  },
  computer: {
    eyebrow: 'TOOLS', title: 'Computer control', description: 'Computer control is an explicit native capability and stays unavailable until the platform permission is granted.',
    rows: [
      { label: 'Control channel', detail: 'Native desktop interaction bridge', value: 'Unavailable' },
      { label: 'Approval mode', detail: 'Confirm each external action', value: 'Ask before action' },
    ],
  },
  history: {
    eyebrow: 'TOOLS', title: 'History', description: 'Session history will be stored locally and remain reviewable before any sync is enabled.',
    rows: [
      { label: 'Local history', detail: 'Completed sessions in this workspace', value: '3 sessions' },
      { label: 'Retention', detail: 'How long local session metadata is kept', value: 'Until removed' },
    ],
  },
  snapshots: {
    eyebrow: 'TOOLS', title: 'App snapshots', description: 'Snapshots make the current UI and event state easy to inspect during development.',
    rows: [
      { label: 'Snapshot capture', detail: 'Capture a reviewable app state', value: 'Available in native shell' },
      { label: 'Last snapshot', detail: 'Most recent saved visual state', value: 'None' },
    ],
  },
  plugins: {
    eyebrow: 'EXTENSIONS', title: 'Plugins', description: 'Install signed extensions for providers, tools, MCP servers, skills, panels, and workflows.',
    rows: [
      { label: 'Installed plugins', detail: 'Extensions active in this workspace', value: '0 installed' },
      { label: 'Plugin permissions', detail: 'Manifest review before activation', value: 'Required' },
    ],
  },
  browser: {
    eyebrow: 'TOOLS', title: 'Browser', description: 'Browser access is opt-in and remains separate from the local workspace until a connector is configured.',
    rows: [
      { label: 'Browser connector', detail: 'Session used for browser tools', value: 'Not connected' },
      { label: 'External pages', detail: 'Allow a tool to inspect an open page', value: 'Ask before access' },
    ],
  },
}

function Icon({ name }: { name: 'plus' | 'search' | 'chevron' | 'folder' | 'chat' | 'spark' | 'terminal' | 'file' | 'git' | 'settings' | 'send' | 'lock' | 'panel' }) {
  const paths: Record<string, string> = {
    plus: 'M12 5v14M5 12h14', search: 'm21 21-4.35-4.35M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4Z', chevron: 'm9 18 6-6-6-6', folder: 'M3.5 6.8h6l1.5 1.8h9.5v9.9H3.5V6.8Z', chat: 'M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 19 17.5H9l-4.5 3v-13A1.5 1.5 0 0 1 5 5.5Z', spark: 'M12 3 13.7 9.3 20 11l-6.3 1.7L12 19l-1.7-6.3L4 11l6.3-1.7L12 3Z', terminal: 'm5 7 5 5-5 5m7 0h7', file: 'M6 3.5h7l5 5V20H6V3.5Zm7 0V9h5', git: 'm8 12 4-4 4 4-4 4', settings: 'M12 8.7a3.3 3.3 0 1 0 0 6.6 3.3 3.3 0 0 0 0-6.6Zm0-5.2v2m0 13.5v2M3.5 12h2m13 0h2M5.9 5.9l1.4 1.4m9.4 9.4 1.4 1.4m0-12.2-1.4 1.4m-9.4 9.4-1.4 1.4', send: 'm3 11.8 18-8.3-7.3 18-2.4-7.2L3 11.8Zm8.3 2.5L21 3.5', lock: 'M7 10V7a5 5 0 0 1 10 0v3m-11.5 0h13A1.5 1.5 0 0 1 20 11.5v8A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5v-8A1.5 1.5 0 0 1 5.5 10Z', panel: 'M4 5h16v14H4V5Zm6 0v14',
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>
}

export function App() {
  const [events, setEvents] = useState(initialEvents)
  const [input, setInput] = useState('')
  const [activeTab, setActiveTab] = useState<'files' | 'diff' | 'output' | 'plugins'>('files')
  const [notice, setNotice] = useState('')
  const [model, setModel] = useState('gpt-5.6-terra')
  const [activeView, setActiveView] = useState<AppView>('workspace')
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('general')
  const [clientState] = useState<'disconnected' | 'connecting' | 'ready' | 'error'>('disconnected')
  const client = useMemo(() => new CodexAppServerClient(new UnavailableTransport()), [])
  const currentProvider = providers.find((provider) => provider.id === 'openai')!

  function submit() {
    const trimmed = input.trim()
    if (!trimmed) return
    if (client.state !== 'ready') {
      setNotice('未发送：Codex App Server 尚未连接。配置本地 app-server 后再发送。')
      setEvents((current) => [{ time: new Date().toLocaleTimeString('zh-CN', { hour12: false }), kind: 'notice', title: 'Request held', detail: 'Transport unavailable · no request sent', tone: 'active' }, ...current])
      return
    }
    setInput('')
  }

  function openSettings(section: SettingsSection = 'general') {
    setSettingsSection(section)
    setActiveView('settings')
  }

  const activeSettings = settingsMeta[settingsSection]
  const settingsGroups = [...new Set(settingsSections.map((section) => section.group))]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup"><div className="brand-mark"><span>◒</span></div><div><strong>cat codex</strong><small>agent workbench</small></div></div>
        <div className="topbar-context"><span className="context-dot" /> {activeView === 'settings' ? 'Settings' : <>New project <span className="slash">/</span> local</>}</div>
        <div className="topbar-actions"><button className="icon-button" aria-label="Toggle panels"><Icon name="panel" /></button><button className={`icon-button ${activeView === 'settings' ? 'active' : ''}`} aria-label="Settings" onClick={() => openSettings()}><Icon name="settings" /></button><div className="avatar">NG</div></div>
      </header>

      {activeView === 'workspace' ? <div className="workspace-grid">
        <aside className="sidebar">
          <div className="sidebar-actions"><button className="new-button"><Icon name="plus" /> New session</button><button className="icon-button subtle" aria-label="Search sessions"><Icon name="search" /></button></div>
          <div className="sidebar-heading"><span>Projects</span><button className="tiny-button" aria-label="Expand projects"><Icon name="chevron" /></button></div>
          <div className="project-row active"><span className="project-glyph">N</span><span className="project-copy"><strong>New project</strong><small>~/Documents/Codex</small></span><span className="project-count">3</span></div>
          <div className="sidebar-heading session-heading"><span>Sessions</span><span className="session-count">3</span></div>
          <nav className="session-list" aria-label="Sessions">{sessions.map((session) => <button key={session.name} className={`session-row ${session.selected ? 'selected' : ''}`}><span className="session-icon"><Icon name="chat" /></span><span className="session-copy"><strong>{session.name}</strong><small>{session.subtitle}</small></span><time>{session.time}</time></button>)}</nav>
          <div className="sidebar-bottom"><button className="sidebar-link" onClick={() => setActiveTab('plugins')}><Icon name="spark" /> Plugin registry <span className="sidebar-pill">0</span></button><button className="sidebar-link"><Icon name="folder" /> Open folder</button><button className="sidebar-link" onClick={() => openSettings()}><Icon name="settings" /> Preferences <kbd>⌘ ,</kbd></button></div>
        </aside>

        <main className="conversation">
          <div className="conversation-header"><div><p className="eyebrow">SESSION · 001</p><h1>Cat Codex first pass</h1></div><div className="header-tools"><span className="local-chip"><span className="chip-dot" /> Local workspace</span><button className="icon-button subtle" aria-label="More session actions">•••</button></div></div>
          <div className="conversation-scroll">
            <section className="welcome-block"><div className="welcome-icon"><span>◒</span></div><div><h2>Ready when you are.</h2><p>Ask Cat Codex to inspect, plan, or change this workspace. Every action will appear in the event stream.</p></div></section>
            <section className="request-card"><div className="request-meta"><span className="request-avatar">NG</span><span>You</span><time>Today, 09:40</time></div><p>先检查仓库规则和现状，搭一个可启动的 Cat Codex 工作台骨架。</p></section>
            <section className="agent-section"><div className="section-label"><span className="live-line" /> Agent events <span className="event-count">{events.length}</span></div><div className="event-stream">{events.map((event, index) => <div className={`event-row ${event.tone === 'active' ? 'event-active' : ''}`} key={`${event.time}-${index}`}><div className={`event-icon event-${event.kind}`}><Icon name={event.kind === 'thought' ? 'spark' : event.kind === 'tool' ? 'terminal' : event.kind === 'file' ? 'file' : 'lock'} /></div><div className="event-body"><div><strong>{event.title}</strong>{event.tone === 'active' && <span className="working-badge">waiting</span>}</div><p>{event.detail}</p></div><time>{event.time}</time></div>)}</div></section>
            <section className="connection-note"><div className="note-icon"><Icon name="lock" /></div><div><strong>App Server connection is off</strong><p>Cat Codex is local-first. Set an app-server endpoint in the native shell to enable conversations.</p></div><button onClick={() => setNotice('连接配置将在 Tauri/native transport 接入阶段开放。')}>Learn how</button></section>
          </div>
          <div className="composer-wrap"><div className="composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) submit() }} placeholder="Ask Cat Codex anything about this workspace…" rows={2} /><div className="composer-footer"><div className="composer-tools"><button className="composer-tool"><Icon name="plus" /> Add context</button><button className="composer-tool"><Icon name="folder" /> Files</button><span className="shortcut-hint">⌘↵ to send</span></div><button className="send-button" onClick={submit} aria-label="Send message"><Icon name="send" /></button></div></div>{notice && <div className="composer-notice" role="status">{notice}<button onClick={() => setNotice('')}>Dismiss</button></div>}</div>
        </main>

        <aside className="inspector"><div className="inspector-tabs" role="tablist">{(['files', 'diff', 'output', 'plugins'] as const).map((tab) => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'files' ? 'Files' : tab === 'diff' ? 'Diff' : tab === 'output' ? 'Output' : 'Plugins'}{tab === 'diff' && <span className="tab-count">2</span>}{tab === 'plugins' && <span className="tab-count muted-count">0</span>}</button>)}</div>{activeTab === 'files' && <div className="inspector-content"><div className="tree-root"><Icon name="folder" /><strong>New project</strong><span>14 files</span></div><div className="file-tree"><div className="tree-row"><Icon name="folder" /><span>apps</span><Icon name="chevron" /></div><div className="tree-row indent"><Icon name="folder" /><span>LaunchMath</span><Icon name="chevron" /></div><div className="tree-row indent"><Icon name="folder" /><span>cat-codex</span><span className="new-marker">new</span></div><div className="tree-row"><Icon name="file" /><span>README.md</span></div><div className="tree-row"><Icon name="file" /><span>package.json</span></div><div className="tree-row"><Icon name="file" /><span>sources.yaml</span></div></div><div className="inspector-section"><div className="inspector-label">WORKSPACE</div><div className="stat-line"><span>Branch</span><strong><Icon name="git" /> main</strong></div><div className="stat-line"><span>Last indexed</span><strong>just now</strong></div></div></div>}{activeTab === 'diff' && <div className="inspector-content"><div className="diff-summary"><span className="diff-add">+ 318</span><span className="diff-remove">− 0</span><span className="diff-files">4 files</span></div><pre className="diff-preview"><code><span className="code-muted">apps/cat-codex/</span>{'\n'}<span className="code-add">+ src/App.tsx</span>{'\n'}<span className="code-add">+ src/styles.css</span>{'\n'}<span className="code-add">+ src/lib/codex/client.ts</span>{'\n'}<span className="code-add">+ src/lib/providers.ts</span></code></pre><p className="empty-copy">Changes stay local until you review and apply them.</p></div>}{activeTab === 'output' && <div className="inspector-content output-panel"><div className="output-status"><span className="status-dot" /> No run yet</div><p>Start the workspace check from the native shell to stream command output here.</p><button className="outline-button"><Icon name="terminal" /> Open terminal</button></div>}{activeTab === 'plugins' && <div className="inspector-content plugins-panel"><div className="plugin-header"><div><p className="eyebrow">EXTENSION POINTS</p><h3>Plugin registry</h3></div><span className="plugin-count">{installedPlugins.length} installed</span></div><p className="plugin-intro">Plugins can add a provider, tool, MCP server, skill, panel, or workflow. Nothing is active in this workspace yet.</p><div className="plugin-list">{(['provider', 'tool', 'mcp', 'skill', 'panel', 'workflow'] as PluginExtension[]).map((extension) => <div className="plugin-slot" key={extension}><span className="slot-dot" /><span>{extensionLabels[extension]}</span><span className="slot-state">Not installed</span></div>)}</div><button className="outline-button" onClick={() => setNotice('插件安装入口会在签名 manifest 与权限审查完成后开放。')}><Icon name="plus" /> Add plugin</button></div>}
          <div className="inspector-footer"><div className="footer-status"><span className={`status-dot ${clientState === 'ready' ? 'ready' : ''}`} /><span>{clientState === 'ready' ? 'Connected' : 'Not connected'}</span></div><label className="model-select"><span>Model</span><select value={model} onChange={(event) => setModel(event.target.value)}>{currentProvider.models.map((item) => <option key={item}>{item}</option>)}</select><Icon name="chevron" /></label><div className="permission-row"><Icon name="lock" /><span>Ask before changes</span><button aria-label="Change permissions">⌄</button></div></div>
        </aside>
      </div> : <section className="settings-shell" aria-label="Settings">
        <aside className="settings-nav">
          <div className="settings-nav-header"><button className="settings-back" onClick={() => setActiveView('workspace')} aria-label="Back to workspace"><Icon name="chevron" /></button><div><strong>Settings</strong><small>Cat Codex</small></div></div>
          <label className="settings-search"><Icon name="search" /><input aria-label="Search settings" placeholder="Search settings" /></label>
          <nav className="settings-section-list">{settingsGroups.map((group) => <div key={group}><p className="settings-group-label">{group}</p>{settingsSections.filter((section) => section.group === group).map((section) => <button key={section.id} className={`settings-nav-item ${settingsSection === section.id ? 'selected' : ''}`} onClick={() => setSettingsSection(section.id)}><Icon name={section.id === 'plugins' ? 'spark' : section.id === 'permissions' ? 'lock' : section.id === 'browser' || section.id === 'computer' ? 'panel' : 'settings'} />{section.label}</button>)}</div>)}</nav>
          <div className="settings-nav-footer"><span className="status-dot" /> Native shell features are off</div>
        </aside>
        <main className="settings-content"><header className="settings-header"><div><p className="eyebrow">{activeSettings.eyebrow}</p><h1>{activeSettings.title}</h1><p>{activeSettings.description}</p></div><button className="back-workspace" onClick={() => setActiveView('workspace')}>Back to workspace <Icon name="chevron" /></button></header><div className="settings-scroll"><section className="settings-card"><div className="settings-card-label">CURRENT CONFIGURATION</div>{activeSettings.rows.map((row) => <div className="setting-row" key={row.label}><div><strong>{row.label}</strong><p>{row.detail}</p></div><span className={`setting-value ${row.value.includes('Not') || row.value === 'Off' || row.value === 'Unavailable' ? 'muted' : ''}`}>{row.value}</span></div>)}</section><section className="settings-footnote"><Icon name="lock" /><div><strong>Settings are local-first</strong><p>Changes that require the native shell, a provider, or an external account will stay unavailable until that boundary is connected.</p></div></section></div></main>
      </section>}
    </div>
  )
}
