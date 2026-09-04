import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { CodexAppServerClient } from './lib/codex/client'
import { TauriTransport, UnavailableTransport } from './lib/codex/transport'
import type { JsonRpcServerRequest } from './lib/codex/types'
import { providers, type ModelProvider, type ProviderId } from './lib/providers'
import { extensionLabels, installedPlugins, type PluginExtension } from './lib/plugins'

type EventKind = 'thought' | 'tool' | 'file' | 'notice'
type AgentEvent = { time: string; kind: EventKind; title: string; detail: string; tone?: 'active' | 'muted' }
type AppView = 'home' | 'workspace' | 'settings'
type SettingsSection = 'general' | 'import' | 'profile' | 'appearance' | 'models' | 'voice' | 'configuration' | 'personalization' | 'companion' | 'shortcuts' | 'usage' | 'account' | 'permissions' | 'computer' | 'history' | 'snapshots' | 'plugins' | 'browser' | 'hooks' | 'providers' | 'language' | 'connections' | 'git' | 'environment' | 'worktrees' | 'archived'
type ProviderEntry = ModelProvider & { baseUrl?: string; credentialEnv?: string; configured?: boolean }
type ProviderForm = { name: string; note: string; baseUrl: string; apiFormat: string; credentialEnv: string; model: string; apiKey: string; toolSearch: boolean; disableBeta: boolean; imageGeneration: boolean; settingsJson: string }

const providerKeyLinks: Partial<Record<ProviderId, string>> = {
  openai: 'https://platform.openai.com/api-keys',
  anthropic: 'https://console.anthropic.com/settings/keys',
  google: 'https://aistudio.google.com/app/apikey',
  deepseek: 'https://platform.deepseek.com/api_keys',
  grok: 'https://console.x.ai/',
  mistral: 'https://console.mistral.ai/api-keys/',
  zhipu: 'https://bigmodel.cn/usercenter/apikeys',
  kimi: 'https://platform.moonshot.cn/console/api-keys',
  minimax: 'https://platform.minimaxi.com/user-center/basic-information/interface-key',
  qwen: 'https://bailian.console.aliyun.com/?tab=model#/api-key',
  qianfan: 'https://console.bce.baidu.com/iam/#/iam/apikey/list',
  openrouter: 'https://openrouter.ai/keys',
  groq: 'https://console.groq.com/keys',
  together: 'https://api.together.ai/settings/api-keys',
  fireworks: 'https://fireworks.ai/account/api-keys',
  ollama: 'https://ollama.com/',
  'lm-studio': 'https://lmstudio.ai/',
  'azure-openai': 'https://portal.azure.com/',
  bedrock: 'https://console.aws.amazon.com/bedrock/',
  'github-models': 'https://github.com/settings/tokens',
}

function readStored<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    return raw === null ? fallback : JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeStored<T>(key: string, value: T) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Local-first settings remain usable when storage is unavailable.
  }
}

function readProviderEntries(): ProviderEntry[] {
  const saved = readStored<ProviderEntry[]>('cat-codex-provider-entries', providers)
  const savedById = new Map(saved.map((entry) => [entry.id, entry]))
  return providers.map((catalogEntry) => {
    const savedEntry = savedById.get(catalogEntry.id)
    if (!savedEntry) return catalogEntry
    if (savedEntry.configured) return { ...catalogEntry, ...savedEntry }
    return { ...catalogEntry, baseUrl: savedEntry.baseUrl, credentialEnv: savedEntry.credentialEnv }
  })
}

const initialEvents: AgentEvent[] = [
  { time: '09:41:18', kind: 'thought', title: 'Agent is waiting', detail: 'Connect Codex App Server to start a turn.', tone: 'active' },
  { time: '09:40:52', kind: 'file', title: 'Workspace indexed', detail: '14 files · 2 directories · local only', tone: 'muted' },
  { time: '09:40:48', kind: 'notice', title: 'Permission profile', detail: 'Ask before changes · network off', tone: 'muted' },
]

const sessions = [
  { name: 'Cat Codex first pass', subtitle: 'App Server workbench', time: '09:41', selected: true },
  { name: 'Provider boundary review', subtitle: 'providers.ts', time: 'Yesterday' },
  { name: 'Plugin registry audit', subtitle: 'plugins.ts', time: 'Aug 28' },
]

const sessionCopy = [
  { name: 'Cat Codex 初次检查', subtitle: 'App Server 工作台', time: '09:41' },
  { name: '服务商边界检查', subtitle: 'providers.ts', time: '昨天' },
  { name: '插件注册表审计', subtitle: 'plugins.ts', time: '8 月 28 日' },
]

const eventCopy: Record<string, { title: string; detail: string }> = {
  'Agent is waiting': { title: '智能体正在等待', detail: '连接 Codex App Server 后即可开始回合。' },
  'Workspace indexed': { title: '工作区已建立索引', detail: '14 个文件 · 2 个目录 · 仅本地' },
  'Permission profile': { title: '权限配置', detail: '更改前询问 · 网络已关闭' },
  'Request held': { title: '请求已暂停', detail: '传输不可用 · 请求未发送' },
}

const settingsSections: Array<{ id: SettingsSection; label: string; group: string }> = [
  { id: 'general', label: 'General', group: 'Personal' }, { id: 'import', label: 'Import', group: 'Personal' }, { id: 'profile', label: 'Profile', group: 'Personal' }, { id: 'appearance', label: 'Appearance', group: 'Personal' }, { id: 'voice', label: 'Voice', group: 'Personal' }, { id: 'configuration', label: 'Configuration', group: 'Personal' }, { id: 'personalization', label: 'Personalization', group: 'Personal' }, { id: 'companion', label: 'Companion', group: 'Personal' }, { id: 'shortcuts', label: 'Keyboard shortcuts', group: 'Personal' }, { id: 'usage', label: 'Usage & billing', group: 'Personal' }, { id: 'account', label: 'Account', group: 'Personal' },
  { id: 'computer', label: 'Computer control', group: 'Integrations' }, { id: 'history', label: 'Computer history', group: 'Integrations' }, { id: 'snapshots', label: 'App snapshots', group: 'Integrations' }, { id: 'plugins', label: 'Plugins', group: 'Integrations' }, { id: 'browser', label: 'Browser', group: 'Integrations' }, { id: 'providers', label: 'Providers', group: 'Integrations' }, { id: 'language', label: 'Language', group: 'Integrations' },
  { id: 'hooks', label: 'Hooks', group: 'Coding' }, { id: 'connections', label: 'Connections', group: 'Coding' }, { id: 'git', label: 'Git', group: 'Coding' }, { id: 'environment', label: 'Environment', group: 'Coding' }, { id: 'worktrees', label: 'Worktrees', group: 'Coding' },
  { id: 'archived', label: 'Archived chats', group: 'Archived' },
]

const settingsMeta: Record<SettingsSection, { eyebrow: string; title: string; description: string; rows: Array<{ label: string; detail: string; value: string }> }> = {
  general: {
    eyebrow: 'WORKSPACE', title: 'General', description: 'Set the defaults that shape each Cat Codex workspace.',
    rows: [
      { label: '默认权限', detail: '默认情况下，Cat Codex 可以读取和编辑工作区中的文件。', value: '开启' },
      { label: '完整访问权限', detail: '允许编辑电脑上的任意文件并运行可访问网络的命令。', value: '开启' },
      { label: 'Projectless task folder', detail: 'Tasks started outside projects store their data here.', value: '/Users/mac/Documents/Codex' },
      { label: '默认文件打开位置', detail: '默认打开文件和文件夹的位置', value: 'VS Code' },
      { label: '在菜单栏中显示', detail: '关闭主窗口后，仍在 macOS 菜单栏中保留 Cat Codex', value: '开启' },
      { label: '底部面板', detail: '在应用标题栏中显示底部面板控件', value: '开启' },
      { label: '默认终端位置', detail: '选择终端快捷键和环境操作在何处打开终端标签页', value: '底部' },
      { label: '运行时防止系统休眠', detail: '在 Cat Codex 运行任务时，让电脑保持唤醒状态', value: '关闭' },
      { label: '速度', detail: '选择 Cat Codex 在聊天、子智能体和压缩中的运行速度', value: '快速' },
      { label: '插件', detail: '允许 Cat Codex 使用已安装插件', value: '开启' },
    ],
  },
  import: {
    eyebrow: 'PERSONAL', title: 'Import', description: 'Bring conversations and settings into Cat Codex.',
    rows: [{ label: 'Import data', detail: 'Import from a supported ChatGPT export', value: 'Available' }],
  },
  profile: {
    eyebrow: 'PERSONAL', title: 'Profile', description: 'Manage the name and identity shown in your workspace.',
    rows: [{ label: 'Display name', detail: 'Shown in conversations and local history', value: 'NG' }],
  },
  language: { eyebrow: 'INTEGRATIONS', title: 'Language', description: 'Choose the display language for Cat Codex.', rows: [] },
  configuration: { eyebrow: 'PERSONAL', title: 'Configuration', description: 'Configure Cat Codex defaults.', rows: [{ label: 'Defaults', detail: 'Workspace defaults', value: 'Ready' }] },
  personalization: { eyebrow: 'PERSONAL', title: 'Personalization', description: 'Customize your Cat Codex experience.', rows: [{ label: 'Style', detail: 'Response preferences', value: 'Default' }] },
  companion: { eyebrow: 'PERSONAL', title: 'Companion', description: 'Manage companion behavior.', rows: [{ label: 'Companion', detail: 'Desktop companion visibility', value: 'On' }] },
  connections: { eyebrow: 'CODING', title: 'Connections', description: 'Manage workspace connections.', rows: [{ label: 'Connections', detail: 'External development connections', value: 'Not configured' }] },
  git: { eyebrow: 'CODING', title: 'Git', description: 'Configure Git integration.', rows: [{ label: 'Git status', detail: 'Repository integration', value: 'Ready' }] },
  environment: { eyebrow: 'CODING', title: 'Environment', description: 'Local environments tell Cat Codex how to set up worktrees for projects. Learn more.', rows: [{ label: 'Environment', detail: 'Runtime environment', value: 'Local' }] },
  worktrees: { eyebrow: 'CODING', title: 'Worktrees', description: '', rows: [{ label: 'Worktrees', detail: 'Worktree locations', value: 'None' }] },
  archived: { eyebrow: 'ARCHIVED', title: 'Archived chats', description: 'Review archived conversations.', rows: [{ label: 'Archived chats', detail: 'Conversations moved out of recent history', value: '0 chats' }] },
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
  providers: {
    eyebrow: 'CODING', title: 'Providers', description: 'Manage API providers and local model gateways. Secrets stay in the native shell.',
    rows: [
      { label: 'Configured providers', detail: 'Providers available to the model picker', value: '1 available' },
      { label: 'Default provider', detail: 'Used for new sessions', value: 'OpenAI / Codex' },
      { label: 'Secret storage', detail: 'API keys and OAuth tokens', value: 'Native shell only' },
    ],
  },
  hooks: {
    eyebrow: 'CODING', title: 'Hooks', description: 'Review lifecycle hooks that can observe or validate workspace actions.',
    rows: [
      { label: 'Session hooks', detail: 'Run before and after a Codex turn', value: 'Not configured' },
      { label: 'Change guard', detail: 'Validate file changes before apply', value: 'Off' },
      { label: 'Secret boundary', detail: 'Hook commands run in the native shell', value: 'Local only' },
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

function Icon({ name }: { name: 'plus' | 'search' | 'chevron' | 'folder' | 'chat' | 'mic' | 'spark' | 'terminal' | 'file' | 'git' | 'hook' | 'settings' | 'send' | 'lock' | 'panel' | 'user' | 'sun' | 'sliders' | 'bot' | 'keyboard' | 'chart' | 'monitor' | 'history' | 'camera' | 'puzzle' | 'browser' | 'link' | 'archive' | 'logout' | 'back' | 'forward' | 'bell' | 'collapse' | 'split' | 'minimize' }) {
  const paths: Record<string, string> = {
    plus: 'M12 5v14M5 12h14', search: 'm21 21-4.35-4.35M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4Z', chevron: 'm9 18 6-6-6-6', folder: 'M3.5 6.8h6l1.5 1.8h9.5v9.9H3.5V6.8Z', chat: 'M5 5.5h14a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 19 17.5H9l-4.5 3v-13A1.5 1.5 0 0 1 5 5.5Z', mic: 'M12 3.5a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0v-5a3 3 0 0 0-3-3ZM6.5 11.5a5.5 5.5 0 0 0 11 0M12 17v3.5m-3 0h6', spark: 'M12 3 13.7 9.3 20 11l-6.3 1.7L12 3Z', terminal: 'm5 7 5 5-5 5m7 0h7', file: 'M6 3.5h7l5 5V20H6V3.5Zm7 0V9h5', git: 'm8 12 4-4 4 4-4 4', hook: 'M12 3v8m0 0a3.5 3.5 0 1 0 3.5 3.5M12 11a3.5 3.5 1 1 1-3.5 3.5M8.5 14.5v2.2a3.5 3.5 0 0 0 7 0v-2.2M5 19.5h14', settings: 'M12 8.7a3.3 3.3 0 1 0 0 6.6 3.3 3.3 0 0 0 0-6.6Zm0-5.2v2m0 13.5v2M3.5 12h2m13 0h2M5.9 5.9l1.4 1.4m9.4 9.4 1.4 1.4m0-12.2-1.4 1.4m-9.4 9.4-1.4 1.4', send: 'm3 11.8 18-8.3-7.3 18-2.4-7.2L3 11.8Zm8.3 2.5L21 3.5', lock: 'M7 10V7a5 5 0 0 1 10 0v3m-11.5 0h13A1.5 1.5 0 0 1 20 11.5v8A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5v-8A1.5 1.5 0 0 1 5.5 10Z', panel: 'M4 5h16v14H4V5Zm6 0v14', user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0', sun: 'M12 3v2m0 14v2M3 12h2m14 0h2M5.6 5.6 7 7m10 10 1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4M12 7.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9Z', sliders: 'M4 6h16M4 12h16M4 18h16M8 4v4m8 2v4m-5 4v4', bot: 'M8 9h8a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3v-5a3 3 0 0 1 3-3Zm4-6v3m-3 7h.01m6-.01h.01', keyboard: 'M4 6h16v12H4V6Zm3 4h.01m3 0h.01m3 0h.01m3 0h.01M7 14h10', chart: 'M5 19V9m5 10V5m5 14v-7m5 7V3', monitor: 'M4 5h16v11H4V5Zm5 15h6m-3-4v4', history: 'M12 7v5l3 2m5-2a8 8 0 1 1-2.3-5.7', camera: 'M4 8h4l1.5-2h5L16 8h4v11H4V8Zm4 5a4 4 0 1 0 8 0 4 4 0 0 0-8 0Z', puzzle: 'M8 4h3a2 2 0 1 1 4 0h3v4a2 2 0 1 1 0 4v4h-4a2 2 0 1 1-4 0H6v-4a2 2 0 1 1 0-4V4h2Z', browser: 'M4 5h16v14H4V5Zm0 4h16M8 7h.01m3 0h.01', link: 'M9.5 14.5 8 16a3.5 3.5 0 0 0 5 5l2.5-2.5a3.5 3.5 0 0 0 0-5M14.5 9.5 16 8a3.5 3.5 0 0 0-5-5L8.5 5.5a3.5 3.5 0 0 0 0 5m-2 2h11', archive: 'M4 7h16v13H4V7Zm-1-3h18v3H3V4Zm5 8h8', logout: 'M10 17l5-5-5-5m5 5H3m8-7V3h8v18h-8v-2',
  }
  paths.spark = 'M12 3 13.7 9.3 20 11l-6.3 1.7L12 19l-1.7-6.3L4 11l6.3-1.7L12 3Z'
  paths.back = 'm15 18-6-6 6-6'
  paths.forward = 'm9 6 6 6-6 6'
  paths.bell = 'M6 10a6 6 0 0 1 12 0c0 7 2 7 2 7H4s2 0 2-7Zm4 9h4'
  paths.collapse = 'M4 4h6v6H4V4Zm10 0h6v6h-6V4ZM4 14h6v6H4v-6Zm10 0h6v6h-6v-6Z'
  paths.split = 'M4 5h16v14H4V5Zm8 0v14'
  paths.minimize = 'M5 12h14'
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]} /></svg>
}

const providerDisplayOrder: ProviderId[] = ['deepseek', 'minimax', 'anthropic', 'openai', 'grok', 'google', 'mistral', 'openrouter', 'openai-compatible']
const providerDisplayCopy: Record<string, { name: string; note: string; baseUrl: string; apiFormat: string; credentialEnv: string; tag?: string }> = {
  deepseek: { name: 'DeepSeek', note: 'DeepSeek', baseUrl: 'https://api.deepseek.com/anthropic', apiFormat: 'Anthropic Messages（原生）', credentialEnv: 'ANTHROPIC_AUTH_TOKEN', tag: '默认' },
  minimax: { name: 'MiniMax', note: 'MiniMax', baseUrl: 'https://coding.dashscope.aliyuncs.com/v1', apiFormat: 'OpenAI Responses', credentialEnv: 'MINIMAX_API_KEY', tag: 'OpenAI Responses' },
  anthropic: { name: 'Claude 官方', note: '', baseUrl: 'https://api.anthropic.com', apiFormat: 'Anthropic Messages（原生）', credentialEnv: 'ANTHROPIC_API_KEY' },
  openai: { name: 'ChatGPT 官方', note: '', baseUrl: 'https://api.openai.com/v1', apiFormat: 'OpenAI Responses', credentialEnv: 'OPENAI_API_KEY' },
  grok: { name: 'Grok 官方', note: '', baseUrl: 'https://api.x.ai/v1', apiFormat: 'OpenAI Responses', credentialEnv: 'XAI_API_KEY' },
  google: { name: 'Gemini 官方', note: '', baseUrl: 'https://generativelanguage.googleapis.com/v1beta', apiFormat: 'OpenAI Chat Completions', credentialEnv: 'GEMINI_API_KEY' },
  mistral: { name: 'Mistral 官方', note: '', baseUrl: 'https://api.mistral.ai/v1', apiFormat: 'OpenAI Chat Completions', credentialEnv: 'MISTRAL_API_KEY' },
  openrouter: { name: 'OpenRouter', note: '', baseUrl: 'https://openrouter.ai/api/v1', apiFormat: 'OpenAI Chat Completions', credentialEnv: 'OPENROUTER_API_KEY' },
  'openai-compatible': { name: '自定义服务商', note: '自定义', baseUrl: '', apiFormat: 'OpenAI Chat Completions', credentialEnv: 'CUSTOM_API_KEY' },
}

function ProviderManagerPage({ providerEntries, onOpen, onAdd, language }: { providerEntries: ProviderEntry[]; onOpen: (id: ProviderId) => void; onAdd: () => void; language: 'zh' | 'en' }) {
  const byId = new Map(providerEntries.map((entry) => [entry.id, entry]))
  return <section className="provider-manager">
    <div className="provider-manager-head"><div><div className="settings-card-label">{language === 'zh' ? 'API 连接' : 'API CONNECTIONS'}</div><h2>{language === 'zh' ? '服务商' : 'Service providers'}</h2></div><div className="provider-manager-actions"><button className="soft-button" onClick={() => window.alert('cc-switch 导入将在原生外壳接入后开放。')}>↧ {language === 'zh' ? '从 cc-switch 导入' : 'Import from cc-switch'}</button><button className="accent-button" onClick={onAdd}><Icon name="plus" /> {language === 'zh' ? '添加服务商' : 'Add provider'}</button></div></div>
    <div className="provider-list provider-reference-list">{providerDisplayOrder.map((id) => { const entry = byId.get(id); const copy = providerDisplayCopy[id]; if (!entry || !copy) return null; const active = id === 'deepseek'; return <article className={`provider-card provider-reference-card ${active ? 'active' : ''}`} key={id} onClick={() => onOpen(id)}><span className="provider-drag" aria-hidden="true">⠿</span><div className="provider-status-dot" data-status={active ? 'ready' : entry.status} /><div className="provider-card-copy"><div className="provider-title-row"><strong>{copy.name}</strong>{copy.note && <span className="provider-name-tag">{copy.note}</span>}{copy.tag && <span className={`provider-badge ${active ? 'default' : ''}`}>{copy.tag}</span>}</div><p>{active ? `${copy.baseUrl} · ${entry.models[0]}` : copy.note ? `${copy.baseUrl} · ${entry.models[0]}` : (id === 'anthropic' ? 'Anthropic 原生接入 — 无需 API 密钥' : id === 'openai' ? '通过 ChatGPT 账号完成 OpenAI OAuth — 无需 API 密钥' : '通过 xAI 账号完成 Grok 官方 OAuth — 无需 API 密钥')}</p></div></article> })}</div>
  </section>
}

function ProviderToggle({ on, label, onChange }: { on: boolean; label: string; onChange: (value: boolean) => void }) {
  return <button type="button" className={`toggle ${on ? 'on' : ''}`} aria-label={label} aria-pressed={on} onClick={() => onChange(!on)}><span /></button>
}

function ProviderDialog({ providerEntries, providerPreset, providerForm, providerKeyUrl, language, setProviderPreset, setProviderForm, onClose, onSave, onTest }: { providerEntries: ProviderEntry[]; providerPreset: ProviderId; providerForm: ProviderForm; providerKeyUrl: string; language: 'zh' | 'en'; setProviderPreset: (id: ProviderId) => void; setProviderForm: (value: ProviderForm) => void; onClose: () => void; onSave: (event: FormEvent<HTMLFormElement>) => void; onTest: () => void }) {
  const presets = providerDisplayOrder.map((id) => providerEntries.find((entry) => entry.id === id)).filter(Boolean) as ProviderEntry[]
  const update = (key: keyof ProviderForm, value: string | boolean) => setProviderForm({ ...providerForm, [key]: value })
  const modelPairs = providerForm.model ? [providerForm.model, providerEntries.find((entry) => entry.id === providerPreset)?.models[1] ?? 'deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-v4-flash'] : []
  return <div className="provider-dialog-backdrop" role="presentation" onMouseDown={onClose}><form className="provider-dialog provider-dialog-reference" onSubmit={onSave} onMouseDown={(event) => event.stopPropagation()}><div className="provider-dialog-head"><div><p className="eyebrow">{language === 'zh' ? '编码 / 服务商' : 'CODING / PROVIDERS'}</p><h2>{language === 'zh' ? '编辑服务商' : 'Edit provider'}</h2></div><button type="button" className="provider-close-button" onClick={onClose} aria-label={language === 'zh' ? '关闭' : 'Close'}>×</button></div>
    <div className="provider-presets">{presets.map((entry) => <button type="button" key={entry.id} className={providerPreset === entry.id ? 'selected' : ''} onClick={() => setProviderPreset(entry.id)}>{providerDisplayCopy[entry.id]?.note || entry.shortName}</button>)}</div>
    <label>{language === 'zh' ? '名称' : 'Name'}<input value={providerForm.name} onChange={(event) => update('name', event.target.value)} required /></label><label>{language === 'zh' ? '备注' : 'Note'}<input value={providerForm.note} onChange={(event) => update('note', event.target.value)} placeholder={language === 'zh' ? '可选备注…' : 'Optional note…'} /></label><label>{language === 'zh' ? '接口地址' : 'Base URL'}<input value={providerForm.baseUrl} onChange={(event) => update('baseUrl', event.target.value)} /></label>
    <label>{language === 'zh' ? 'API 格式' : 'API format'}<select value={providerForm.apiFormat} onChange={(event) => update('apiFormat', event.target.value)}><option>Anthropic Messages（原生）</option><option>OpenAI Responses</option><option>OpenAI Chat Completions</option></select></label><label>{language === 'zh' ? '认证变量' : 'Credential environment variable'}<select value={providerForm.credentialEnv} onChange={(event) => update('credentialEnv', event.target.value)}><option>{providerForm.credentialEnv || 'ANTHROPIC_AUTH_TOKEN'}</option><option>ANTHROPIC_API_KEY</option><option>OPENAI_API_KEY</option><option>MINIMAX_API_KEY</option></select></label>
    <div className="provider-option-card"><ProviderToggle on={providerForm.toolSearch} onChange={(value) => update('toolSearch', value)} label="启用 Tool Search" /><div><strong>启用 Tool Search</strong><p>默认关闭。仅当模型和最终上游都支持 tool_reference 时启用。</p></div></div><div className="provider-option-card"><ProviderToggle on={providerForm.disableBeta} onChange={(value) => update('disableBeta', value)} label="关闭实验性 Beta 头" /><div><strong>关闭实验性 Beta 头</strong><p>为此服务商设置 CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1，避免第三方通道拒绝 beta API 形态。</p></div></div>
    <label>{language === 'zh' ? 'API 密钥' : 'API key'}<div className="provider-secret-field"><input type="password" value={providerForm.apiKey} onChange={(event) => update('apiKey', event.target.value)} placeholder="••••••••" autoComplete="off" /><span aria-hidden="true">◉</span></div></label>{providerKeyUrl && <a className="provider-key-link" href={providerKeyUrl} target="_blank" rel="noreferrer">⌕ {language === 'zh' ? '获取 API Key ↗' : 'Get API key ↗'}</a>}
    <div className="provider-option-card provider-toggle-row"><ProviderToggle on={providerForm.imageGeneration} onChange={(value) => update('imageGeneration', value)} label="启用图片生成" /><div><strong>启用图片生成</strong><p>允许聊天通过 OpenAI 兼容的 Images API 生图。凭证保存在服务商设置中，不写进 Skill。</p></div></div>
    <div className="provider-model-heading"><div><h3>{language === 'zh' ? '模型映射' : 'Model mapping'}</h3><p>仅当上游服务商提供模型列表接口时才能获取。</p></div><button type="button" className="soft-button" onClick={onTest}>♨ {language === 'zh' ? '获取模型' : 'Fetch models'}</button></div><div className="provider-model-grid">{modelPairs.map((model, index) => <label key={`${model}-${index}`}>{['主模型', 'Haiku 模型', 'Sonnet 模型', 'Opus 模型'][index]}<input value={model} onChange={(event) => index === 0 && update('model', event.target.value)} readOnly={index !== 0} /></label>)}</div>
    <button type="button" className="soft-button provider-test-button" onClick={onTest}>{language === 'zh' ? '测试连接' : 'Test connection'}</button><label>{language === 'zh' ? '设置 JSON' : 'Settings JSON'}<textarea className="provider-json" value={providerForm.settingsJson} onChange={(event) => update('settingsJson', event.target.value)} /></label><p className="provider-dialog-note"><Icon name="lock" /> {language === 'zh' ? '原始密钥不会存储在网页界面中。' : 'Raw secrets are never stored in the web UI.'}</p><div className="provider-dialog-actions"><button type="button" className="outline-button" onClick={onClose}>{language === 'zh' ? '取消' : 'Cancel'}</button><button type="submit" className="accent-button">{language === 'zh' ? '保存' : 'Save'}</button></div>
  </form></div>
}

function PersonalizationPage({ instructions, setInstructions, memoryEnabled, setMemoryEnabled, setNotice }: { instructions: string; setInstructions: (value: string) => void; memoryEnabled: boolean; setMemoryEnabled: (value: boolean) => void; setNotice: (value: string) => void }) {
  return <section className="personalization-page">
    <section className="personalization-block"><div className="personalization-heading"><div><h2>自定义指令</h2><p>向 Cat Codex 提供适用于此工作区的额外说明和上下文。 <a href="#learn">了解更多</a></p></div><button className="soft-button" disabled={!instructions.trim()} onClick={() => setNotice('自定义指令已保存。')}>保存</button></div><textarea className="instruction-editor" value={instructions} onChange={(event) => setInstructions(event.target.value)} placeholder="告诉 Cat Codex 你希望它如何工作……" /></section>
    <section className="personalization-block"><h2>记忆</h2><p>设置在此电脑上如何收集、保留和整合本地记忆。 <a href="#learn">了解更多</a></p><div className="settings-card memory-card"><div className="setting-row"><div><strong>启用本地记忆</strong><p>根据此电脑上的聊天创建记忆，并用于个性化该电脑上的后续聊天</p></div><button className={`toggle ${memoryEnabled ? 'on' : ''}`} onClick={() => setMemoryEnabled(!memoryEnabled)} aria-label="启用本地记忆"><span /></button></div><div className="setting-row"><div><strong>允许基于工具辅助聊天生成本地记忆</strong><p>从使用过 MCP 工具或网页搜索的聊天生成记忆</p></div><button className="toggle on" aria-label="允许工具记忆"><span /></button></div><div className="setting-row"><div><strong>删除本地记忆</strong><p>删除存储在此电脑本地的所有记忆</p></div><button className="danger-button" onClick={() => setNotice('本地记忆删除操作需要确认。')}>删除</button></div></div></section>
    <div className="personalization-note"><span>!</span> 并非所有模型都支持个性化设置。可在自定义指令中调整 Cat Codex 的语气。</div><div className="settings-card"><div className="setting-row"><div><strong>个性</strong><p>选择 Cat Codex 回复的默认语气</p></div><span className="select-like">亲和⌄</span></div></div>
  </section>
}

function ImportPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="import-page"><h2>导入</h2><p className="page-description">将其他 AI 应用的设置、项目和聊天导入 Cat Codex</p><h3>开启自动同步</h3><div className="settings-card"><div className="setting-row"><div><strong>保持导入同步</strong><p>自动同步已连接来源中的新增和更新内容</p></div><button className="toggle" aria-label="保持导入同步"><span /></button></div></div><h3>从其他 AI 应用导入</h3><p className="page-description">检测到可添加到 Cat Codex 的配置</p><div className="settings-card import-sources">{['Claude Code','Claude Cowork','Cursor'].map((name) => <div className="setting-row" key={name}><div className="import-source"><span className="source-mark">{name === 'Cursor' ? '➤' : '</>'}</span><strong>{name}</strong></div><button className="soft-button" onClick={() => setNotice(`${name} 导入已准备。`)}>导入</button></div>)}</div></section>
}

function CompanionPage({ setNotice }: { setNotice: (value: string) => void }) {
  const pets = [['◒', 'Codex', '原版 Codex 智能伙伴。'], ['◈', 'Dewey', '适合专注工作日的平静伙伴。'], ['♨', 'Fireball', '为快速迭代提供热情能量。'], ['◉', 'Hoots', '敏锐的猫头鹰，帮助你快速完成精细工作。'], ['◇', 'Rocky', '差异变大时依然稳健可靠。'], ['♧', 'Seedy', '为新想法长出小小的绿色嫩芽。'], ['▦', 'Stacky', '适合深度工作的平衡伙伴。'], ['▣', 'BSOD', '一只小小的蓝屏捣蛋鬼。'], ['◌', 'Null Signal', '来自虚空的安静信号。']]
  return <section className="companion-page"><div className="companion-heading"><div><h2>智能伙伴</h2><p>宠物会管理对话，并突出显示需要关注的事项</p></div><div className="companion-actions"><button className="soft-button" onClick={() => setNotice('宠物列表已刷新。')}>↻</button><button className="soft-button" onClick={() => setNotice('创建宠物入口将在本地资源目录连接后开放。')}>创建</button><button className="soft-button" onClick={() => setNotice('宠物已收起。')}>收起宠物</button></div></div><div className="settings-card pet-list">{pets.map(([symbol, name, detail], index) => <div className="pet-row" key={name}><span className={`pet-avatar pet-${index}`}>{symbol}</span><div><strong>{name}</strong><p>{detail}</p></div><button className="soft-button" disabled={index === 0} onClick={() => setNotice(`${name} 已选中。`)}>{index === 0 ? '已选' : '选择'}</button></div>)}<div className="custom-pet-row"><div><strong>自定义宠物</strong><p>/Users/mac/.codex/pets</p></div><button className="text-button" onClick={() => setNotice('正在打开自定义宠物文件夹。')}>打开文件夹 ↗</button></div></div><h3>外观</h3><div className="settings-card"><div className="setting-row"><div><strong>宠物大小</strong><p>调整宠物大小</p></div><input className="pet-size" type="range" min="60" max="140" defaultValue="100" aria-label="宠物大小" /></div></div></section>
}

function ShortcutsPage({ setNotice }: { setNotice: (value: string) => void }) {
  const shortcuts = [['新聊天','开始新聊天','⌘N'],['新建临时聊天','开始聊天，此聊天不会显示在历史记录中','⇧⌘N'],['快速聊天','在快速编辑器中开始轻量聊天','⌥⌘N'],['归档聊天','归档当前聊天','⇧⌘A'],['新建独立聊天','在项目外开始新聊天','⌥⌘O'],['打开侧边聊天','在侧边聊天中打开当前聊天','⌥⌘S'],['标记为未读','将当前聊天标记为未读','⇧⌘U'],['在新窗口中打开','在新窗口中打开当前聊天','未分配'],['切换置顶状态','置顶或取消置顶当前聊天','⌥⌘P'],['聚焦浏览器地址栏','聚焦应用内浏览器地址栏','⌘L'],['聚焦主聊天输入框','将键盘焦点移至主聊天输入框','未分配'],['聚焦侧边聊天','将键盘焦点移至已打开的侧边聊天输入框','未分配'],['转到行','转到当前文件中的某一行','⌘L'],['返回','在导航历史记录中返回','⌘[ · Mouse Back'],['前进','在导航历史记录中前进','⌘] · Mouse Forward'],['下一个最近查看的聊天','切换到下一个最近查看的聊天','⌃Tab'],['下一个标签页','切换到下一个标签页','⇧⌘]'],['下一个聊天','切换到下一个聊天','⇧⌘Right'],['切换到工作','切换到工作','⌃2'],['切换到 Codex','切换到 Codex','⌃3'],['打开浏览器标签页','打开新浏览器标签页','⌘T'],['打开审查选项卡','打开“审阅”选项卡','⌃⇧G'],['切换底部面板','显示或隐藏底部面板','⌘J'],['显示/隐藏浏览器面板','显示或隐藏浏览器面板','⇧⌘B'],['打开终端','打开终端面板','⌃`'],['提交或推送','打开提交或推送选项','未分配'],['创建分支','打开分支创建选项','未分配'],['创建草稿 PR','打开草稿 Pull Request 创建选项','未分配']]
  return <section className="shortcuts-page"><div className="shortcuts-heading"><h2>键盘快捷键</h2><button className="soft-button" onClick={() => setNotice('快捷键已恢复默认值。')}>全部重置为默认值</button></div><label className="shortcut-search"><Icon name="search" /><input placeholder="搜索快捷键" aria-label="搜索快捷键" /><span>↯</span></label><div className="settings-card shortcut-list">{shortcuts.map(([name, detail, keys]) => <div className="shortcut-row" key={name}><div><strong>{name}</strong><p>{detail}</p></div><div className="shortcut-controls"><span className={keys === '未分配' ? 'unassigned' : 'keycaps'}>{keys}</span><button aria-label={`编辑${name}`} onClick={() => setNotice(`正在编辑：${name}`)}>⌕</button><button aria-label={`删除${name}`} onClick={() => setNotice(`已删除快捷键：${name}`)}>♧</button></div></div>)}</div></section>
}

function UsagePage({ setNotice }: { setNotice: (value: string) => void }) {
  const Meter = ({ label, detail, percent }: { label: string; detail: string; percent: number }) => <div className="usage-meter"><div><strong>{label}</strong><p>{detail}</p></div><div className="meter-value"><span className="meter-track"><span style={{ width: `${percent}%` }} /></span><em>剩余 {100 - percent}%</em></div></div>
  return <section className="usage-page"><h2>使用情况和计费</h2><p className="page-description">如需查看发票、更改付款方式或进行其他操作，请前往网页版 <a href="#settings">设置</a></p><h3>当前套餐</h3><div className="settings-card"><div className="setting-row"><div><strong>Pro 套餐</strong><p>₽9,990/月</p></div><button className="soft-button" onClick={() => setNotice('套餐详情将在账户连接后打开。')}>查看套餐</button></div></div><h3>额度余额</h3><p className="page-description">购买额度或启用自动充值，达到限额后仍可继续使用 Codex。 <a href="#learn">了解更多</a></p><div className="settings-card"><div className="setting-row"><div><strong>PHP 0</strong><p>当前余额</p></div><button className="soft-button" onClick={() => setNotice('购买额度将在账户连接后开放。')}>购买额度</button></div><div className="setting-row"><div><strong>自动充值</strong><p>达到上限后仍可继续工作</p></div><div className="autofill-control"><span>最高可享 40% 折扣</span><button className="toggle" aria-label="自动充值"><span /></button></div></div><div className="setting-row"><div><strong>为他人购买额度</strong></div><button className="soft-button" onClick={() => setNotice('赠送额度将在账户连接后开放。')}>赠送额度</button></div></div><h3>通用使用限额</h3><div className="settings-card"><Meter label="每周使用限额" detail="重置时间：2026年9月6日 09:00" percent={15} /></div><h3>GPT-5.3-Codex-Spark 使用限额</h3><div className="settings-card"><Meter label="5 小时使用限额" detail="重置时间：00:20" percent={0} /><Meter label="每周使用限额" detail="重置时间：2026年9月6日 19:20" percent={0} /></div><h3>使用限额重置</h3><div className="settings-card"><div className="setting-row"><div><strong>完全重置</strong><p>将于 9/21 GMT+8 14:25 到期</p></div><button className="dark-button" onClick={() => setNotice('正在使用重置额度。')}>使用重置额度</button></div></div><h3>取消套餐</h3><p className="page-description">您的订阅由 Cat Codex 管理。如需取消套餐，请前往 <a href="#billing">账单</a> 操作。</p></section>
}

function ComputerPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="computer-page"><h2>电脑操控</h2><p className="page-description">管理 Cat Codex 如何使用你电脑上的其他应用程序</p><h3>控制</h3><div className="settings-card app-control-card"><div className="app-control-row"><span className="app-icon chrome">◉</span><div><strong>Google Chrome</strong><p><i className="status-dot ready" /> 已安装浏览器扩展程序</p></div><button className="soft-button" onClick={() => setNotice('Chrome 管理设置已打开。')}>管理</button><button className="toggle on" aria-label="Google Chrome"><span /></button></div><div className="app-control-row"><span className="app-icon excel">X</span><div><strong>Microsoft Excel</strong><p>允许 Cat Codex 使用 Microsoft Excel 加载项以获得更多控制权限</p></div><button className="toggle on" aria-label="Microsoft Excel"><span /></button></div></div><div className="settings-card lock-control"><div className="app-control-row"><span className="app-icon lock-app">▣</span><div><strong>锁屏操作</strong><p>允许 Cat Codex 在 Mac 锁定时使用此 Mac。 <a href="#learn">了解更多</a></p></div><button className="toggle" aria-label="锁屏操作"><span /></button></div></div><h3>始终允许的应用</h3><div className="settings-card empty-apps">暂无</div></section>
}

function HistoryPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="history-page"><h2>计算机历史记录</h2><div className="history-hero"><div className="history-copy"><h3>让 Cat Codex 关注你的工作</h3><p>Cat Codex 可以总结你在所用应用和网站中的活动，且绝不会录制你的屏幕或音频。</p><p>询问你之前正在处理的事项，无需再次解释一切即可获得帮助，或发现自动化重复任务的机会。</p><button className="dark-button" onClick={() => setNotice('计算机历史记录已请求开启。')}>开启</button></div><div className="history-preview"><div className="history-preview-card">昨天会后，我答应给 Sarah 发邮件？<hr /><span>你在 Slack 上告诉 Sarah，会在周五前发送 Q3 预算。最新版在 Google Sheets 中，你在 Google Docs 中的会议记录列出两个待确认的数字：招聘和差旅。</span></div><div className="preview-dots">● ● ●</div></div></div><p className="history-note">开启后，Cat Codex 会保存你在允许的应用和网站中的活动文本摘要，可能包括通信内容。音频和私密模式网页浏览绝不会包含在内；你可以随时暂停或清除历史记录，并管理包含的内容。此功能会增加 Token 用量。 <a href="#learn">了解更多</a></p></section>
}

function SnapshotsPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="snapshots-page"><h2>应用快照</h2><div className="snapshot-banner"><span className="snapshot-mark">▣</span><div><strong>截取应用快照，向 Cat Codex 展示你最前端的窗口</strong><p>智能快照包含视觉和文本内容，包括滚动到屏幕外的文本。</p></div></div><div className="snapshot-grid"><div className="settings-card"><div className="setting-row"><div><strong>快捷键</strong><p>同时按下两个 ⌘ 键</p></div><span className="select-like">⌘ + ⌘⌄</span></div><div className="setting-row"><div><strong>Appshot 发送目标</strong><p>选择使用快捷键时将 appshots 发送到哪里</p></div><span className="select-like">自动⌄</span></div><div className="setting-row"><div><strong>播放音效</strong></div><button className="toggle on" aria-label="播放音效"><span /></button></div></div><div className="snapshot-preview"><div className="snapshot-window"><div className="snapshot-bar" /><div className="snapshot-lines" /><div className="snapshot-keyboard" /></div></div></div></section>
}

function BrowserPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="browser-page"><h2>浏览器</h2><p className="page-description">管理内置浏览器。可在<a href="#computer">计算机使用设置</a>中设置浏览器扩展程序</p><div className="settings-card browser-toggle-card"><div className="setting-row"><div className="browser-label"><span className="browser-app-icon">⌁</span><div><strong>浏览器</strong><p>让 Cat Codex 控制内置浏览器</p></div></div><button className="toggle on" aria-label="浏览器"><span /></button></div></div><div className="browser-heading"><h3>常规</h3><button className="soft-button" onClick={() => setNotice('浏览器设置导入入口已打开。')}>导入…</button></div><div className="settings-card"><div className="setting-row"><div><strong>网页 URL 和链接打开位置</strong><p>链接默认打开位置</p></div><span className="select-like">默认浏览器⌄</span></div><div className="setting-row"><div><strong>本地 URL 打开位置</strong><p>本地开发站点默认打开位置</p></div><span className="select-like">ChatGPT⌄</span></div><div className="setting-row"><div><strong>浏览数据</strong><p>清除应用内浏览器中的浏览历史记录、网站数据、缓存和下载历史</p></div><button className="soft-button" onClick={() => setNotice('应用内浏览数据已清除。')}>清除浏览数据</button></div><div className="setting-row"><div><strong>浏览历史</strong><p>查看和管理在内置浏览器中访问过的页面</p></div><button className="soft-button" onClick={() => setNotice('浏览历史管理入口已打开。')}>管理</button></div><div className="setting-row"><div><strong>批注截图</strong><p>截图可帮助 Cat Codex 更好地理解和处理评论，但会增加套餐费用</p></div><span className="select-like">始终包含⌄</span></div></div><h3>自动填充和密码</h3><div className="settings-card"><div className="setting-row"><div><strong>密码管理器</strong><p>添加、删除和编辑已保存的密码</p></div><button className="soft-button" onClick={() => setNotice('密码管理器需要原生浏览器连接。')}>管理</button></div><div className="setting-row"><div><strong>联系信息</strong><p>添加、删除和编辑已保存的地址、电话号码和电子邮箱地址</p></div><button className="soft-button" onClick={() => setNotice('联系信息管理入口已打开。')}>管理</button></div></div><h3>下载</h3><div className="settings-card"><div className="setting-row"><div><strong>位置</strong><p>系统下载文件夹</p></div><button className="soft-button" onClick={() => setNotice('下载位置选择需要原生外壳。')}>更改</button></div><div className="setting-row"><div><strong>下载前询问保存位置</strong><p>对在内置浏览器中发起的下载显示保存对话框</p></div><button className="toggle" aria-label="下载前询问保存位置"><span /></button></div><div className="setting-row"><div><strong>下载历史记录</strong><p>查看和管理从内置浏览器下载的文件</p></div><button className="soft-button" onClick={() => setNotice('下载历史管理入口已打开。')}>管理</button></div></div><h3>权限</h3><div className="settings-card"><div className="setting-row"><div><strong>网站设置</strong><p>管理内置浏览器中的摄像头和麦克风权限</p></div><button className="soft-button" onClick={() => setNotice('网站权限管理入口已打开。')}>管理</button></div><div className="setting-row"><div><strong>审批</strong><p>选择 Cat Codex 在打开网站前是否请求批准。 <a href="#learn">了解更多</a></p></div><span className="select-like">始终允许⌄</span></div><div className="setting-row"><div><strong>历史记录</strong><p>选择 Cat Codex 是否可访问你的内置浏览器历史记录</p></div><span className="select-like">始终询问⌄</span></div><div className="setting-row"><div><strong>下载</strong><p>选择 Cat Codex 从网站下载文件前是否先询问</p></div><span className="select-like">始终询问⌄</span></div><div className="setting-row"><div><strong>上传</strong><p>选择 Cat Codex 在将文件上传到网站前是否先询问</p></div><span className="select-like">始终询问⌄</span></div><div className="setting-row"><div><strong>启用站点工具</strong><p>允许 Cat Codex 发现并调用网站公开的站点工具，包括 WebMCP</p></div><button className="toggle on" aria-label="启用站点工具"><span /></button></div></div><div className="browser-heading"><div><h3>网站权限</h3><p className="page-description">为特定网站覆盖上述默认设置</p></div><button className="soft-button" onClick={() => setNotice('网站权限添加入口已打开。')}>＋ 添加</button></div><div className="settings-card site-permission"><div><strong>https://oss.console.aliyun.com</strong><p><i className="status-dot ready" /> 上传</p></div><div className="row-actions"><span className="select-like">⚙ 自定义⌄</span><button className="icon-action" onClick={() => setNotice('网站权限已移除。')}>♧</button></div></div><p className="browser-note">这里只显示设置了自定义权限的网站</p><h3>开发者模式</h3><div className="settings-card developer-mode"><div className="setting-row"><div><strong className="risk-label">ⓘ 风险升高</strong><strong>启用完整 CDP 访问权限</strong><p>允许 Cat Codex 在已连接的 Browser Use 会话中使用完整的 Chrome DevTools Protocol (CDP) 访问权限。完整 CDP 访问权限可让 Cat Codex 检查并控制敏感的浏览器内部功能，可能使你的数据面临风险。</p></div><button className="toggle on" aria-label="启用完整 CDP 访问权限"><span /></button></div></div></section>
}

function HooksPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="hooks-page">
    <h2>钩子</h2>
    <p className="page-description">通过配置和已启用的插件管理生命周期钩子。 <a href="#learn">了解更多</a></p>
    <button className="hooks-refresh" aria-label="刷新钩子" onClick={() => setNotice('钩子配置已刷新。')}>↻</button>
    <h3>来自配置</h3>
    <button className="settings-card hook-source-card" onClick={() => setNotice('用户配置中的钩子详情将在配置连接后打开。')}>
      <span className="hook-source-icon"><Icon name="settings" /></span>
      <span className="hook-source-copy"><strong>用户配置</strong><small>11 个钩子</small></span>
      <span className="hook-source-status"><b>!</b><strong>11 项待审核</strong><Icon name="chevron" /></span>
    </button>
  </section>
}

function ConnectionsPage({ setNotice }: { setNotice: (value: string) => void }) {
  const [tab, setTab] = useState<'mac' | 'other' | 'ssh'>('mac')
  const [allowConnection, setAllowConnection] = useState(true)
  const [keepAwake, setKeepAwake] = useState(true)
  const [hasDevice, setHasDevice] = useState(true)
  const tabs: Array<{ id: 'mac' | 'other' | 'ssh'; label: string }> = [
    { id: 'mac', label: '控制这台 Mac' },
    { id: 'other', label: '控制其他设备' },
    { id: 'ssh', label: 'SSH' },
  ]

  const selectTab = (nextTab: 'mac' | 'other' | 'ssh') => {
    setTab(nextTab)
    if (nextTab !== 'mac') setNotice(`${tabs.find((item) => item.id === nextTab)?.label}连接暂不可用。`)
  }

  return <section className="connections-page">
    <h2>连接</h2>
    <div className="connection-tabs" role="tablist" aria-label="连接类型">
      {tabs.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} className={`connection-tab ${tab === item.id ? 'selected' : ''}`} onClick={() => selectTab(item.id)}>{item.label}</button>)}
    </div>
    {tab === 'mac' ? <>
      <div className="connections-section-heading">
        <h3>可控制这台 Mac 的设备</h3>
        <div className="connections-heading-actions">
          <button type="button" className="icon-action" aria-label="刷新设备" onClick={() => setNotice('设备列表已刷新。')}>↻</button>
          <button type="button" className="dark-button" onClick={() => { setHasDevice(true); setNotice('已恢复截图中的预览设备（仅本地预览）。') }}>添加</button>
        </div>
      </div>
      <div className="settings-card connections-device-card">
        <div className="setting-row connections-allow-row"><div><strong>允许连接</strong></div><button type="button" className={`toggle ${allowConnection ? 'on' : ''}`} aria-label="允许连接" aria-pressed={allowConnection} onClick={() => { const next = !allowConnection; setAllowConnection(next); setNotice(next ? '已允许设备连接。' : '已暂停设备连接。') }}><span /></button></div>
        {hasDevice ? <div className="connection-authorized-device">
          <span className="connection-phone-icon" aria-hidden="true"><i /></span>
          <span className="connection-device-copy"><strong>iOS 26.5.2 iPhone</strong><small>上次连接时间 2 周</small></span>
          <button type="button" className="soft-button" onClick={() => { setHasDevice(false); setNotice('已从本地预览中撤销设备访问权限。') }}>撤销访问权限</button>
        </div> : <div className="connection-empty-state"><div className="connection-device-pair" aria-hidden="true"><span className="connection-device phone" /><span className="connection-device-dots">•••</span><span className="connection-device laptop"><i /></span></div><p>暂无已授权设备</p><button type="button" className="dark-button" onClick={() => { setHasDevice(true); setNotice('已恢复截图中的预览设备（仅本地预览）。') }}>添加</button></div>}
      </div>
      <h3>其他设置</h3>
      <div className="settings-card"><div className="setting-row connection-awake-row"><span className="connection-awake-icon"><Icon name="sun" /></span><div><strong>让这台 Mac 保持唤醒状态</strong><p>当电脑接通电源且启用远程访问时，防止其进入睡眠状态</p></div><button type="button" className={`toggle ${keepAwake ? 'on' : ''}`} aria-label="保持唤醒状态" aria-pressed={keepAwake} onClick={() => { const next = !keepAwake; setKeepAwake(next); setNotice(next ? '已开启保持唤醒状态。' : '已关闭保持唤醒状态。') }}><span /></button></div></div>
    </> : <div className="settings-card connection-tab-placeholder"><strong>{tabs.find((item) => item.id === tab)?.label}</strong><p>该连接方式将在原生工作台连接后可用。</p><button type="button" className="soft-button" onClick={() => setNotice('连接服务尚未配置。')}>了解状态</button></div>}
  </section>
}

function GitPage({ setNotice, language }: { setNotice: (value: string) => void; language: 'zh' | 'en' }) {
  const [branchPrefix, setBranchPrefix] = useState('codex/')
  const [mergeMethod, setMergeMethod] = useState<'merge' | 'squash'>('merge')
  const [forcePush, setForcePush] = useState(false)
  const [draftPullRequest, setDraftPullRequest] = useState(true)
  const [reviewMode, setReviewMode] = useState<'inline' | 'separate'>('inline')
  const [autoMerge, setAutoMerge] = useState(false)
  const [autoMergeInstructions, setAutoMergeInstructions] = useState('')
  const [commitInstructions, setCommitInstructions] = useState('')
  const [pullRequestInstructions, setPullRequestInstructions] = useState('')

  const t = (zh: string, en: string) => language === 'zh' ? zh : en
  const notifyLocal = () => setNotice(t('Git 设置已更新（仅本地预览）。', 'Git settings updated (local preview only).'))
  const Toggle = ({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) => <button type="button" className={`toggle ${value ? 'on' : ''}`} aria-label={label} aria-pressed={value} onClick={() => { onChange(!value); notifyLocal() }}><span /></button>
  const Segment = ({ label, selected, onSelect }: { label: string; selected: boolean; onSelect: () => void }) => <button type="button" className={`git-segment ${selected ? 'selected' : ''}`} aria-pressed={selected} onClick={() => { onSelect(); notifyLocal() }}>{label}</button>

  return <section className="git-page">
    <h2>Git</h2>
    <div className="settings-card git-settings-card">
      <div className="setting-row">
        <div><strong>{t('分支前缀', 'Branch prefix')}</strong><p>{t('ChatGPT 创建新分支时使用的前缀', 'Prefix used when ChatGPT creates a new branch')}</p></div>
        <input className="git-text-input" value={branchPrefix} onChange={(event) => setBranchPrefix(event.target.value)} onBlur={notifyLocal} aria-label={t('分支前缀', 'Branch prefix')} />
      </div>
      <div className="setting-row">
        <div><strong>{t('拉取请求合并方法', 'Pull request merge method')}</strong><p>{t('选择 ChatGPT 合并拉取请求的方式', 'Choose how ChatGPT merges pull requests')}</p></div>
        <div className="git-segmented" role="group" aria-label={t('拉取请求合并方法', 'Pull request merge method')}><Segment label={t('合并', 'Merge')} selected={mergeMethod === 'merge'} onSelect={() => setMergeMethod('merge')} /><Segment label={t('压缩合并', 'Squash and merge')} selected={mergeMethod === 'squash'} onSelect={() => setMergeMethod('squash')} /></div>
      </div>
      <div className="setting-row">
        <div><strong>{t('始终强制推送', 'Always force push')}</strong><p>{t('从 ChatGPT 推送时使用 --force-with-lease', 'Use --force-with-lease when pushing from ChatGPT')}</p></div>
        <Toggle label={t('始终强制推送', 'Always force push')} value={forcePush} onChange={setForcePush} />
      </div>
      <div className="setting-row">
        <div><strong>{t('创建草稿拉取请求', 'Create draft pull requests')}</strong><p>{t('从 ChatGPT 创建 PR 时默认使用草稿拉取请求', 'Create PRs from ChatGPT as drafts by default')}</p></div>
        <Toggle label={t('创建草稿拉取请求', 'Create draft pull requests')} value={draftPullRequest} onChange={setDraftPullRequest} />
      </div>
      <div className="setting-row">
        <div><strong>{t('审查结果呈现方式', 'Review result presentation')}</strong><p>{t('尽可能在当前聊天中启动 /review，或启动单独的审查聊天', 'Start /review in the current chat when possible, or start a separate review chat')}</p></div>
        <div className="git-segmented" role="group" aria-label={t('审查结果呈现方式', 'Review result presentation')}><Segment label={t('内联', 'Inline')} selected={reviewMode === 'inline'} onSelect={() => setReviewMode('inline')} /><Segment label={t('单独', 'Separate')} selected={reviewMode === 'separate'} onSelect={() => setReviewMode('separate')} /></div>
      </div>
    </div>

    <h3>{t('监控并修复 Pull Request', 'Monitor and fix Pull Requests')}</h3>
    <div className="settings-card git-settings-card">
      <div className="setting-row">
        <div><strong>{t('准备就绪时自动合并', 'Auto-merge when ready')}</strong><p>{t('继续监控，直到 Pull Request 合并', 'Keep monitoring until the Pull Request is merged')}</p></div>
        <Toggle label={t('准备就绪时自动合并', 'Auto-merge when ready')} value={autoMerge} onChange={setAutoMerge} />
      </div>
    </div>
    <textarea className="git-textarea" value={autoMergeInstructions} onChange={(event) => setAutoMergeInstructions(event.target.value)} onBlur={notifyLocal} placeholder={t('例如：检查通过后评论 /merge，并批准不相关的 Chromatic 变更...', 'e.g. comment /merge after checks pass, and approve unrelated Chromatic changes...')} aria-label={t('自动合并说明', 'Auto-merge instructions')} />

    <h3>{t('提交说明', 'Commit instructions')}</h3>
    <p className="git-section-description">{t('将添加到提交信息生成提示中', 'Added to the commit message generation prompt')}</p>
    <textarea className="git-textarea" value={commitInstructions} onChange={(event) => setCommitInstructions(event.target.value)} onBlur={notifyLocal} placeholder={t('添加提交信息指引...', 'Add commit message guidance...')} aria-label={t('提交说明', 'Commit instructions')} />

    <h3>{t('拉取请求说明', 'Pull request instructions')}</h3>
    <p className="git-section-description">{t('将添加到 PR 标题/描述生成提示中', 'Added to the PR title/description generation prompt')}</p>
    <textarea className="git-textarea" value={pullRequestInstructions} onChange={(event) => setPullRequestInstructions(event.target.value)} onBlur={notifyLocal} placeholder={t('添加拉取请求指引...', 'Add pull request guidance...')} aria-label={t('拉取请求说明', 'Pull request instructions')} />
  </section>
}

function EnvironmentPage({ setNotice, language }: { setNotice: (value: string) => void; language: 'zh' | 'en' }) {
  const projects = [
    { name: 'Claude-cc-haha_全部文件' },
    { name: 'Codex' },
    { name: 'Obsidian Vault' },
    { name: 'New project', detail: '354685856-sn' },
    { name: 'ai-info-radar-system' },
    { name: 'Deniro-Tech-AI-Automation' },
  ]
  const [selectedProjects, setSelectedProjects] = useState<Set<string>>(() => new Set())
  const [projectPickerRequested, setProjectPickerRequested] = useState(false)
  const t = (zh: string, en: string) => language === 'zh' ? zh : en
  const toggleProject = (name: string) => {
    const alreadySelected = selectedProjects.has(name)
    setSelectedProjects((current) => {
      const next = new Set(current)
      if (alreadySelected) next.delete(name)
      else next.add(name)
      return next
    })
    setNotice(alreadySelected
      ? t(`${name} 已从当前工作区移除（仅本地预览）。`, `${name} removed from the current workspace (local preview only).`)
      : t(`${name} 已加入当前工作区（仅本地预览）。`, `${name} added to the current workspace (local preview only).`))
  }
  const requestProjectPicker = () => {
    const nextRequested = !projectPickerRequested
    setProjectPickerRequested(nextRequested)
    setNotice(nextRequested
      ? t('添加项目需要连接本地工作区选择器；当前为本地预览。', 'Adding a project requires the local workspace picker; this is a local preview.')
      : t('已关闭添加项目提示。', 'The add-project prompt is closed.'))
  }

  return <section className="environment-page">
    <h2>{t('环境', 'Environment')}</h2>
    <div className="environment-project-heading">
      <h3>{t('选择项目', 'Choose a project')}</h3>
      <button type="button" className="soft-button" aria-expanded={projectPickerRequested} onClick={requestProjectPicker}>{t('添加项目', 'Add project')}</button>
    </div>
    <div className="environment-project-list">
      {projects.map(({ name, detail }) => <article className="environment-project-card" key={name}>
        <div className="environment-project-icon" aria-hidden="true"><Icon name="folder" /></div>
        <div className="environment-project-copy"><strong>{name}</strong>{detail && <p>{detail}</p>}</div>
        <button
          type="button"
          className="environment-project-add"
          data-added={selectedProjects.has(name)}
          aria-label={selectedProjects.has(name) ? t(`从工作区移除 ${name}`, `Remove ${name} from workspace`) : t(`添加 ${name}`, `Add ${name}`)}
          aria-pressed={selectedProjects.has(name)}
          title={selectedProjects.has(name) ? t('从当前工作区移除', 'Remove from current workspace') : t('加入当前工作区', 'Add to current workspace')}
          onClick={() => toggleProject(name)}
        >{selectedProjects.has(name) ? '✓' : '+'}</button>
      </article>)}
    </div>
  </section>
}

function WorktreesPage({ setNotice, language }: { setNotice: (value: string) => void; language: 'zh' | 'en' }) {
  const [fetchBeforeCreate, setFetchBeforeCreate] = useState(false)
  const [autoDelete, setAutoDelete] = useState(true)
  const [retention, setRetention] = useState('15')
  const [rootPath, setRootPath] = useState('/Users/mac/.codex/worktrees')
  const t = (zh: string, en: string) => language === 'zh' ? zh : en
  const notifyLocal = () => setNotice(t('设置已更新（仅本地预览）。', 'Setting updated (local preview only).'))

  return <section className="worktrees-page">
    <h2>{t('工作树', 'Worktrees')}</h2>
    <div className="settings-card worktrees-settings-card">
      <div className="setting-row worktrees-path-row">
        <div><strong>{t('工作树根目录', 'Worktree root directory')}</strong><p>{t('ChatGPT 创建托管工作树的目录。留空则使用默认位置', 'Directory where ChatGPT creates managed worktrees. Leave blank to use the default location')}</p></div>
        <input className="worktrees-path-input" value={rootPath} onChange={(event) => setRootPath(event.target.value)} onBlur={notifyLocal} aria-label={t('工作树根目录', 'Worktree root directory')} />
      </div>
      <div className="setting-row">
        <div><strong>{t('创建工作树前始终获取上游更新', 'Always fetch upstream before creating a worktree')}</strong><p>{t('Codex 通常会在常规 Git 操作中获取分支更新。此设置还会在创建每个新工作树前获取上游更新。', 'Codex usually fetches branch updates during regular Git operations. This also fetches upstream updates before each new worktree is created.')}</p></div>
        <button type="button" className={`toggle ${fetchBeforeCreate ? 'on' : ''}`} aria-label={t('创建工作树前始终获取上游更新', 'Always fetch upstream before creating a worktree')} aria-pressed={fetchBeforeCreate} onClick={() => { setFetchBeforeCreate(!fetchBeforeCreate); notifyLocal() }}><span /></button>
      </div>
      <div className="setting-row">
        <div><strong>{t('自动删除旧工作树', 'Automatically delete old worktrees')}</strong><p>{t('推荐大多数用户启用。仅当你需要手动管理旧工作树和磁盘使用空间时，再关闭此功能。', 'Recommended for most users. Turn this off only if you need to manage old worktrees and disk usage manually.')}</p></div>
        <button type="button" className={`toggle ${autoDelete ? 'on' : ''}`} aria-label={t('自动删除旧工作树', 'Automatically delete old worktrees')} aria-pressed={autoDelete} onClick={() => { setAutoDelete(!autoDelete); notifyLocal() }}><span /></button>
      </div>
      <div className="setting-row">
        <div><strong>{t('自动删除限制', 'Automatic deletion limit')}</strong><p>{t('要保留的托管工作树数量；超过后，较旧的工作树会自动被清理。ChatGPT 会在删除工作树前创建快照，因此被清理的工作树始终可以恢复。', 'Number of managed worktrees to keep. Older worktrees are cleaned up after this limit; ChatGPT creates a snapshot before deletion so cleaned-up worktrees can always be restored.')}</p></div>
        <input className="worktrees-number-input" inputMode="numeric" value={retention} onChange={(event) => setRetention(event.target.value.replace(/[^0-9]/g, ''))} onBlur={notifyLocal} aria-label={t('自动删除限制', 'Automatic deletion limit')} />
      </div>
    </div>

    <div className="worktrees-project-heading">
      <h3>{t('尚无工作树', 'No worktrees yet')}</h3>
      <button type="button" className="worktrees-refresh" aria-label={t('刷新工作树', 'Refresh worktrees')} onClick={() => setNotice(t('工作树列表已刷新（仅本地预览）。', 'Worktree list refreshed (local preview only).'))}>↻</button>
    </div>
    <article className="settings-card worktree-empty-state">
      <p>{t('ChatGPT 创建的工作树将显示在此处', 'Worktrees created by ChatGPT will appear here')}</p>
    </article>
  </section>
}

type ArchivedChat = {
  id: string
  group: 'local' | 'cat-codex'
  zhTitle: string
  enTitle: string
  zhDate: string
  enDate: string
}

const archivedChatSeed: ArchivedChat[] = [
  { id: 'settings-alignment', group: 'local', zhTitle: '设置界面对齐检查', enTitle: 'Settings UI alignment review', zhDate: '8月30日 19:36', enDate: 'Aug 30, 19:36' },
  { id: 'provider-config', group: 'local', zhTitle: '服务商配置测试', enTitle: 'Provider configuration test', zhDate: '8月30日 17:22', enDate: 'Aug 30, 17:22' },
  { id: 'browser-connection', group: 'local', zhTitle: '浏览器连接调试', enTitle: 'Browser connection debugging', zhDate: '8月30日 16:48', enDate: 'Aug 30, 16:48' },
  { id: 'voice-entry', group: 'local', zhTitle: '语音入口检查', enTitle: 'Voice entry review', zhDate: '8月30日 15:56', enDate: 'Aug 30, 15:56' },
  { id: 'theme-comparison', group: 'local', zhTitle: '明暗主题对照', enTitle: 'Light and dark theme comparison', zhDate: '8月29日 22:15', enDate: 'Aug 29, 22:15' },
  { id: 'shortcuts', group: 'local', zhTitle: '键盘快捷键整理', enTitle: 'Keyboard shortcut cleanup', zhDate: '8月29日 19:08', enDate: 'Aug 29, 19:08' },
  { id: 'settings-density', group: 'local', zhTitle: '设置页密度调整', enTitle: 'Settings density tuning', zhDate: '8月29日 18:42', enDate: 'Aug 29, 18:42' },
  { id: 'app-server-events', group: 'cat-codex', zhTitle: 'App Server 事件流设计', enTitle: 'App Server event stream design', zhDate: '8月30日 14:20', enDate: 'Aug 30, 14:20' },
  { id: 'plugin-registry', group: 'cat-codex', zhTitle: '插件注册表审查', enTitle: 'Plugin registry review', zhDate: '8月29日 21:36', enDate: 'Aug 29, 21:36' },
  { id: 'model-routing', group: 'cat-codex', zhTitle: '多模型路由边界', enTitle: 'Multi-model routing boundary', zhDate: '8月29日 16:12', enDate: 'Aug 29, 16:12' },
  { id: 'native-permissions', group: 'cat-codex', zhTitle: '本地外壳权限检查', enTitle: 'Native shell permission review', zhDate: '8月28日 20:05', enDate: 'Aug 28, 20:05' },
]

function ArchivedPage({ setNotice, language }: { setNotice: (value: string) => void; language: 'zh' | 'en' }) {
  const [query, setQuery] = useState('')
  const [chatFilter, setChatFilter] = useState<'all' | 'recent'>('all')
  const [projectFilter, setProjectFilter] = useState<'all' | ArchivedChat['group']>('all')
  const [visibleIds, setVisibleIds] = useState(() => archivedChatSeed.map((chat) => chat.id))
  const t = (zh: string, en: string) => language === 'zh' ? zh : en
  const titleFor = (chat: ArchivedChat) => language === 'zh' ? chat.zhTitle : chat.enTitle
  const dateFor = (chat: ArchivedChat) => language === 'zh' ? chat.zhDate : chat.enDate
  const normalizedQuery = query.trim().toLocaleLowerCase()
  const visibleChats = archivedChatSeed.filter((chat) => visibleIds.includes(chat.id))
    .filter((chat) => projectFilter === 'all' || chat.group === projectFilter)
    .filter((chat) => !normalizedQuery || `${chat.zhTitle} ${chat.enTitle}`.toLocaleLowerCase().includes(normalizedQuery))
    .filter((_, index) => chatFilter === 'all' || index < 5)
  const groups: Array<{ id: ArchivedChat['group']; label: string }> = [
    { id: 'local', label: t('无项目', 'No project') },
    { id: 'cat-codex', label: 'Cat Codex' },
  ]
  const unarchive = (chat: ArchivedChat) => {
    setVisibleIds((current) => current.filter((id) => id !== chat.id))
    setNotice(t(`“${chat.zhTitle}”已从本地预览列表移除；未修改真实聊天。`, `“${chat.enTitle}” was removed from the local preview; no real chat was changed.`))
  }
  const deleteAll = () => {
    setVisibleIds([])
    setNotice(t('已清空本地预览列表；未删除真实聊天。', 'The local preview list was cleared; no real chats were deleted.'))
  }

  return <section className="archived-page">
    <div className="archived-toolbar">
      <label className="archived-search"><Icon name="search" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('搜索已归档聊天', 'Search archived chats')} aria-label={t('搜索已归档聊天', 'Search archived chats')} /></label>
      <select value={chatFilter} onChange={(event) => setChatFilter(event.target.value as 'all' | 'recent')} aria-label={t('聊天筛选', 'Chat filter')}><option value="all">{t('全部聊天', 'All chats')}</option><option value="recent">{t('最近聊天', 'Recent chats')}</option></select>
      <select value={projectFilter} onChange={(event) => setProjectFilter(event.target.value as 'all' | ArchivedChat['group'])} aria-label={t('项目筛选', 'Project filter')}><option value="all">{t('所有项目', 'All projects')}</option><option value="local">{t('无项目', 'No project')}</option><option value="cat-codex">Cat Codex</option></select>
      <button type="button" className="archived-delete-all" disabled={!visibleIds.length} onClick={deleteAll}>⌫ {t('全部删除', 'Delete all')}</button>
    </div>
    <div className="archived-groups">
      {groups.map((group) => {
        const chats = visibleChats.filter((chat) => chat.group === group.id)
        if (!chats.length) return null
        return <section className="archived-group" key={group.id}>
          <header><span className="archived-folder"><Icon name="folder" /></span><strong>{group.label}</strong><span>{t(`${chats.length} 个聊天`, `${chats.length} chats`)}</span>{group.id === 'cat-codex' && <button type="button" aria-label={t('更多项目操作', 'More project actions')}>•••</button>}</header>
          {chats.map((chat) => <article className="archived-chat-row" key={chat.id}>
            <div><strong>{titleFor(chat)}</strong><time>{dateFor(chat)}</time></div>
            <button type="button" className="archived-trash" aria-label={t(`删除 ${chat.zhTitle}`, `Delete ${chat.enTitle}`)} onClick={() => unarchive(chat)}>⌫</button>
            <button type="button" className="soft-button" onClick={() => unarchive(chat)}>{t('取消归档', 'Unarchive')}</button>
          </article>)}
        </section>
      })}
      {!visibleChats.length && <div className="archived-empty"><Icon name="archive" /><strong>{t('没有符合条件的已归档聊天', 'No matching archived chats')}</strong><p>{t('这是本地界面预览，不会修改你的真实聊天记录。', 'This is a local UI preview and does not change your real chat history.')}</p></div>}
    </div>
  </section>
}

function PluginsPage({ setNotice }: { setNotice: (value: string) => void }) {
  const items = [['Plugin Management','发现并管理插件','✣'],['Default templates','为文档、表格和演示文稿提供默认模板','◆'],['Documents','创建和编辑文档','▤'],['PDF','阅读、创建并验证 PDF','PDF'],['Spreadsheets','创建和编辑电子表格','▦'],['Presentations','创建和编辑演示文稿','▣'],['Template Creator','从参考内容创建或更新可复用模板','◆'],['Sites','构建并部署网站','▪'],['Visualize','创建交互式可视化内容','✦']]
  return <section className="plugins-page"><div className="plugins-page-head"><div><h2>插件</h2><p className="page-description">管理插件、技能和 MCP</p></div><div className="plugins-actions"><button className="soft-button" onClick={() => setNotice('正在打开插件目录。')}>浏览目录</button><button className="dark-button" onClick={() => setNotice('添加插件入口已打开。')}>添加⌄</button></div></div><div className="plugin-tabs"><span className="active">插件 <b>9</b></span><span>应用 <b>5</b></span><span>MCP <b>10</b></span><span>技能 <b>29</b></span><label><Icon name="search" /><input placeholder="搜索插件" aria-label="搜索插件" /></label></div><div className="plugin-catalog">{items.map(([name, detail, icon], index) => <div className="catalog-row" key={name}><span className={`catalog-icon icon-${index}`}>{icon}</span><div><strong>{name}</strong><p>{detail}</p></div><button className="toggle on" aria-label={name}><span /></button></div>)}</div></section>
}

function ProfilePage({ setNotice }: { setNotice: (value: string) => void }) {
  const metrics = [['26.8亿', '累计 Token 数'], ['4.2亿', '峰值 Token 数'], ['2 小时 9 分', '最长聊天时长'], ['10 天', '当前连续天数'], ['10 天', '最长连续天数']]
  const plugins = [['🧩', '$change-productivity-stack', '4 次运行'], ['🌐', '@chrome', '3 次运行'], ['🧩', '$change-ui-ux-pro', '1 次运行'], ['◎', '$openai-docs', '1 次运行']]
  return <section className="profile-page"><div className="profile-actions"><button onClick={() => setNotice('邀请好友链接已复制。')}>⌁ 邀请好友</button><button onClick={() => setNotice('分享链接已复制。')}>↥ 分享</button><button>⌕ 私有</button><button onClick={() => setNotice('个人资料编辑入口已打开。')}>✎ 编辑</button></div><div className="profile-identity"><div className="profile-avatar">EM</div><h2>Elizabeth Martinez</h2><p>@patricia-where1981 · <span>Pro</span></p></div><div className="profile-metrics">{metrics.map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div><div className="profile-activity-head"><h3>Token 活动</h3><div><b>每日</b><span>每周</span><span>累计</span></div></div><div className="activity-grid" aria-label="Token 活动"><div className="activity-cells">{Array.from({ length: 168 }, (_, index) => <i className={index % 19 === 0 ? 'hot' : index % 11 === 0 ? 'warm' : ''} key={index} />)}</div><div className="activity-months"><span>9月</span><span>10月</span><span>11月</span><span>12月</span><span>1月</span><span>2月</span><span>3月</span><span>4月</span><span>5月</span><span>6月</span><span>7月</span><span>8月</span></div></div><div className="profile-columns"><div><h3>活动洞察</h3><dl><dt>快速模式</dt><dd>72%</dd><dt>最常用的推理强度</dt><dd>中 · 47%</dd><dt>已探索的技能</dt><dd>4</dd><dt>使用的技能总数</dt><dd>9</dd><dt>聊天总数</dt><dd>2,045</dd></dl></div><div><h3>最常用的插件</h3><ul className="profile-plugin-list">{plugins.map(([icon, name, count]) => <li key={name}><span>{icon}</span><strong>{name}</strong><em>{count}</em></li>)}</ul></div></div></section>
}

function AppearancePage({ setNotice, theme, setTheme }: { setNotice: (value: string) => void; theme: 'system' | 'light' | 'dark'; setTheme: (value: 'system' | 'light' | 'dark') => void }) {
  const [contrast, setContrast] = useState(60)
  const [translucent, setTranslucent] = useState(true)
  const [pointer, setPointer] = useState(false)
  return <section className="appearance-page"><h2>外观</h2><h3>主题</h3><div className="theme-previews"><button className={`theme-preview system ${theme === 'system' ? 'selected' : ''}`} onClick={() => { setTheme('system'); setNotice('已选择系统主题。') }}><span /><b>系统</b></button><button className={`theme-preview light ${theme === 'light' ? 'selected' : ''}`} onClick={() => { setTheme('light'); setNotice('已选择浅色主题。') }}><span /><b>浅色</b></button><button className={`theme-preview dark ${theme === 'dark' ? 'selected' : ''}`} onClick={() => { setTheme('dark'); setNotice('已选择深色主题。') }}><span /><b>深色</b></button></div><div className="theme-code"><code><span>1</span> const themePreview: ThemeConfig = {'{'}<br /><span>2</span> &nbsp;surface: <em>"sidebar"</em>,<br /><span>3</span> &nbsp;accent: <em>"#0ea5e9"</em>,<br /><span>4</span> &nbsp;contrast: <em>{contrast}</em>,<br /><span>5</span> {'}'}</code></div><div className="settings-card appearance-card"><div className="setting-row"><div><strong>浅色主题</strong></div><div className="row-actions"><button onClick={() => setNotice('主题导入需要本地文件选择器。')}>导入</button><button onClick={() => setNotice('主题已复制到剪贴板。')}>复制主题</button><span className="select-like">Aa</span><span className="select-like">Codex⌄</span></div></div><div className="setting-row"><div><strong>强调色</strong></div><span className="color-value accent-color">◯ #339CFF</span></div><div className="setting-row"><div><strong>背景</strong></div><span className="color-value light-color">◯ #FFFFFF</span></div><div className="setting-row"><div><strong>前景</strong></div><span className="color-value dark-color">◯ #1A1C1F</span></div><div className="setting-row"><div><strong>UI 字体</strong></div><div className="row-actions"><span className="select-like">系统默认⌄</span><span className="select-like">常规⌄</span></div></div><div className="setting-row"><div><strong>代码字体</strong></div><div className="row-actions"><span className="select-like">系统默认⌄</span><span className="select-like">常规⌄</span></div></div><div className="setting-row"><div><strong>半透明侧边栏</strong></div><button className={`toggle ${translucent ? 'on' : ''}`} aria-label="半透明侧边栏" aria-pressed={translucent} onClick={() => setTranslucent(!translucent)}><span /></button></div><div className="setting-row"><div><strong>对比度</strong></div><div className="range-value"><input type="range" min="0" max="100" value={contrast} onChange={(event) => setContrast(Number(event.target.value))} aria-label="对比度" /><span>{contrast}</span></div></div></div><h3>偏好设置</h3><div className="settings-card appearance-card"><div className="setting-row"><div><strong>使用指针光标</strong><p>悬停交互元素时切换为指针光标</p></div><button className={`toggle ${pointer ? 'on' : ''}`} aria-label="使用指针光标" aria-pressed={pointer} onClick={() => setPointer(!pointer)}><span /></button></div><div className="setting-row"><div><strong>Dock 图标</strong><p>选择应用在 Dock 中使用的图标</p></div><div className="dock-options"><span>◎</span><span>◒</span></div></div><div className="setting-row"><div><strong>减少动态效果</strong><p>减少动画效果或匹配系统设置</p></div><div className="row-actions"><span className="select-like">系统</span><span>开启</span><span>关闭</span></div></div><div className="setting-row"><div><strong>UI 字号</strong><p>调整 Cat Codex 界面使用的基准字号</p></div><span className="number-input">14 <small>px</small></span></div><div className="setting-row"><div><strong>代码字体大小</strong><p>调整聊天和差异视图中代码使用的基准字号</p></div><span className="number-input">12 <small>px</small></span></div><div className="setting-row"><div><strong>差异标记</strong><p>使用颜色或 +/- 标记显示更改</p></div><div className="row-actions"><span className="select-like">颜色</span><span>+/-</span></div></div><div className="setting-row"><div><strong>字体平滑</strong><p>使用 macOS 原生字体抗锯齿</p></div><button className="toggle on" aria-label="字体平滑"><span /></button></div></div></section>
}

function VoicePage({ setNotice }: { setNotice: (value: string) => void }) {
  const recordings = ['我怎么受不了了。', '录音已取消', '那把我的服务器做的跟这个网址做的服务器一样吗？手机也可以看。', '你现在是停止状态还是工作状态？', '你能听见我说话吗？你能不能听见我说话？']
  return <section className="voice-page"><h2>语音</h2><h3>常规</h3><div className="settings-card"><div className="setting-row"><div><strong>麦克风</strong><p>用于语音聊天和听写</p></div><span className="select-like">系统默认⌄</span></div></div><h3>语音聊天</h3><div className="settings-card"><div className="setting-row"><div><strong>语音</strong><p>选择 Codex 在新语音聊天中使用的语音</p></div><span className="select-like voice-chip">🔵 Cove</span></div><div className="setting-row"><div><strong>语音聊天热键</strong><p>在桌面端任意位置启动语音聊天</p></div><div className="row-actions"><span className="keycaps">Left ⌘</span><button className="icon-action" onClick={() => setNotice('语音聊天热键编辑入口已打开。')}>✎</button><button className="icon-action">♧</button></div></div><div className="setting-row"><div><strong>屏幕上下文</strong><p>当你提到屏幕上的内容时，允许 Codex 查看前台应用。首次访问时 macOS 会请求权限。</p></div><button className="toggle on" aria-label="屏幕上下文"><span /></button></div></div><h3>听写</h3><div className="settings-card"><div className="setting-row"><div><strong>按住听写快捷键</strong><p>在桌面任意位置按住，即可在光标处听写</p></div><div className="row-actions"><span className="keycaps">⌘S</span><button className="icon-action">✎</button><button className="icon-action">♧</button></div></div><div className="setting-row"><div><strong>切换听写快捷键</strong><p>在桌面任意位置按一次开始听写，再按一次停止</p></div><div className="row-actions"><span className="keycaps">⌘K</span><button className="icon-action">✎</button><button className="icon-action">♧</button></div></div><div className="setting-row"><div><strong>保持听写栏可见</strong><p>听写未录制时显示小型快捷键提醒</p></div><button className="toggle on" aria-label="保持听写栏可见"><span /></button></div></div><div className="settings-card voice-dictionary"><div className="setting-row"><div><strong>听写词典</strong><p>听写应能识别的单词或短语</p></div><button className="soft-button" onClick={() => setNotice('已添加听写词条。')}>＋ 添加条目</button></div><input placeholder="Jane Doe" aria-label="听写词典条目" /></div><div className="settings-card recent-recordings"><div className="setting-row"><div><strong>最近录音</strong><p>你最近的 20 段录音会保存在此设备上</p></div></div>{recordings.map((text, index) => <div className="recording-row" key={text}><div><strong>{text}</strong><p>{index === 0 ? '8月29日 17:31' : `8月${26 - index}日 10:41`}</p></div><div className="row-actions"><button className="icon-action">▢</button><button className="icon-action">···</button></div></div>)}</div></section>
}

function ConfigurationPage({ setNotice }: { setNotice: (value: string) => void }) {
  return <section className="configuration-page"><h2>配置</h2><p className="page-description">配置新聊天的权限、网页访问和智能体回复。 <a href="#learn">了解更多</a></p><h3>智能体默认设置</h3><div className="configuration-toolbar"><span className="select-like">用户配置⌄</span><button onClick={() => setNotice('正在打开 config.toml。')}>打开 config.toml ↗</button></div><div className="settings-card"><div className="setting-row"><div><strong>批准策略</strong><p>选择 Cat Codex 何时请求批准</p></div><span className="select-like">按请求⌄</span></div><div className="setting-row"><div><strong>沙盒设置</strong><p>选择 Cat Codex 运行命令时的权限范围</p></div><span className="select-like">只读⌄</span></div><div className="setting-row"><div><strong>网页搜索</strong><p>选择 Cat Codex 访问网络的方式</p></div><span className="select-like">已缓存⌄</span></div><div className="setting-row"><div><strong>输出详细程度</strong><p>选择 Cat Codex 回复包含细节的详细程度</p></div><span className="select-like">模型默认⌄</span></div><div className="setting-row"><div><strong>推理摘要</strong><p>选择 Cat Codex 总结其推理的方式</p></div><span className="select-like">自动⌄</span></div></div><h3>模型功能</h3><div className="settings-card"><div className="setting-row"><div><strong>可用推理强度</strong><p>选择在模型控件中显示哪些推理强度级别。可用性因模型而异</p></div><span className="select-like">已选择 5 个⌄</span></div><div className="setting-row"><div><strong>模型选择器滑块中的 Ultra</strong><p>将 Ultra 显示为滑块最高档选项</p></div><button className="toggle" aria-label="Ultra"><span /></button></div></div><h3>工作空间依赖项</h3><div className="settings-card"><div className="setting-row"><div><strong>Codex 依赖项</strong><p>允许 Cat Codex 安装并提供随附的 Node.js 和 Python 工具</p></div><button className="toggle on" aria-label="Codex 依赖项"><span /></button></div><div className="setting-row"><div><strong>诊断 Cat Codex 工作空间中的问题</strong><p>检查当前捆绑包并记录诊断日志</p></div><button className="soft-button" onClick={() => setNotice('工作空间诊断已启动。')}>⌕ 诊断</button></div><div className="setting-row"><div><strong>重置并安装工作空间</strong><p>下载新的软件包并安装，然后重新加载工具</p></div><button className="danger-button" onClick={() => setNotice('重新安装需要原生工作台确认。')}>⇩ 重新安装</button></div><small className="version-note">当前版本：26.826.12353</small></div></section>
}

function AccountPage() {
  return <section className="account-page"><h2>账户</h2><p className="page-description">管理 Cat Codex 工作台设置。</p><div className="settings-card"><div className="settings-card-label">当前配置</div><div className="setting-row"><div><strong>已登录账户</strong><p>当前服务商使用的身份</p></div><span className="setting-value muted">未连接</span></div><div className="setting-row"><div><strong>工作区同步</strong><p>跨设备同步设置和会话</p></div><span className="setting-value muted">关闭</span></div></div><div className="settings-footnote"><Icon name="lock" /><div><strong>设置以本地优先</strong><p>需要原生外壳、服务商或外部账户的更改，会在边界连接前保持不可用。</p></div></div></section>
}

function LanguagePage({ language, setLanguage }: { language: 'zh' | 'en'; setLanguage: (value: 'zh' | 'en') => void }) {
  return <section className="language-page"><h2>{language === 'zh' ? '语言' : 'Language'}</h2><p className="page-description">{language === 'zh' ? '选择应用程序的显示语言。' : 'Choose the display language for Cat Codex.'}</p><div className="language-options"><button className={language === 'en' ? 'selected' : ''} onClick={() => setLanguage('en')}>English</button><button className={language === 'zh' ? 'selected' : ''} onClick={() => setLanguage('zh')}>简体中文</button></div></section>
}

function GeneralPage({ setNotice, language }: { setNotice: (value: string) => void; language: 'zh' | 'en' }) {
  const [toggleState, setToggleState] = useState<Record<string, boolean>>({})
  const Toggle = ({ on, label }: { on?: boolean; label: string }) => {
    const active = Object.prototype.hasOwnProperty.call(toggleState, label) ? toggleState[label] : Boolean(on)
    return <button className={`toggle ${active ? 'on' : ''}`} aria-label={label} aria-pressed={active} onClick={() => setToggleState((current) => ({ ...current, [label]: !active }))}><span /></button>
  }
  return <section className="general-page"><h3>权限</h3><div className="settings-card"><div className="setting-row"><div><strong>默认权限</strong><p>默认情况下，Cat Codex 可以读取和编辑工作区中的文件。需要时，它可以请求额外访问权限</p></div><Toggle on label="默认权限" /></div><div className="setting-row"><div><strong>完整访问权限</strong><p>当 Cat Codex 以完整访问权限运行时，它无需你的批准即可编辑你电脑上的任何文件，并运行可访问网络的命令。这会显著增加数据丢失、泄露或意外行为的风险。 <a href="#learn">了解更多</a></p></div><Toggle on label="完整访问权限" /></div></div><h3>常规</h3><div className="settings-card general-card"><div className="setting-row"><div><strong>{language === 'zh' ? '项目外任务文件夹' : 'Projectless task folder'}</strong><p>{language === 'zh' ? '任务在项目外启动时默认存储数据的位置' : 'The location where tasks started outside projects store their data by default.'}</p></div><div className="row-actions"><span className="setting-path">/Users/mac/Documents/Codex</span><button className="soft-button" onClick={() => setNotice('任务文件夹更改需要原生工作台确认。')}>更改</button></div></div><div className="setting-row"><div><strong>默认文件打开位置</strong><p>默认打开文件和文件夹的位置</p></div><span className="select-like">▣ VS Code⌄</span></div><div className="setting-row"><div><strong>在菜单栏中显示</strong><p>关闭主窗口后，仍在 macOS 菜单栏中保留 Cat Codex</p></div><Toggle on label="在菜单栏中显示" /></div><div className="setting-row"><div><strong>底部面板</strong><p>在应用标题栏中显示底部面板控件</p></div><Toggle on label="底部面板" /></div><div className="setting-row"><div><strong>默认终端位置</strong><p>选择终端快捷键和环境操作在何处打开终端标签页</p></div><div className="segmented"><span className="selected">底部</span><span>右侧</span></div></div><div className="setting-row"><div><strong>运行时防止系统休眠</strong><p>在 Cat Codex 运行任务时，让电脑保持唤醒状态</p></div><Toggle label="运行时防止系统休眠" /></div><div className="setting-row"><div><strong>速度</strong><p>选择 Cat Codex 在聊天、子智能体和压缩中的运行速度</p></div><span className="select-like">快速⌄</span></div><div className="setting-row"><div><strong>打开源许可证</strong><p>捆绑依赖项的第三方声明</p></div><button className="soft-button" onClick={() => setNotice('许可证页面将在应用窗口中打开。')}>查看</button></div><div className="setting-row"><div><strong>插件</strong><p>允许 Cat Codex 使用已安装插件</p></div><Toggle on label="插件" /></div></div><h3>编辑器</h3><div className="settings-card general-card"><div className="setting-row"><div><strong>纯文本编辑器</strong><p>编写消息时，将代码、Markdown 和链接保留为纯文本</p></div><Toggle label="纯文本编辑器" /></div><div className="setting-row"><div><strong>显示上下文窗口使用情况</strong></div><Toggle label="显示上下文窗口使用情况" /></div><div className="setting-row"><div><strong>发送快捷键</strong><p>选择按 Enter 时是发送提示还是插入新行</p></div><span className="select-like">按 Enter 键⌄</span></div><div className="setting-row"><div><strong>跟进处理方式</strong><p>在 Cat Codex 运行时将后续消息加入队列，或调整当前运行的方向。按 ⌘↵ 可对单条消息执行相反操作</p></div><div className="segmented"><span className="selected">加入队列</span><span>调整方向</span></div></div></div><h3>弹出窗口</h3><div className="settings-card general-card"><div className="setting-row"><div><strong>弹出窗口快捷键</strong><p>为弹出窗口设置全局快捷键。不设置则保持关闭。</p></div><div className="row-actions"><span>关闭</span><button className="icon-action">✎</button></div></div><div className="setting-row"><div><strong>默认使用独立聊天</strong><p>在任何项目外开始新聊天</p></div><Toggle label="默认使用独立聊天" /></div></div><h3>通知</h3><div className="settings-card general-card"><div className="setting-row"><div><strong>轮次完成通知</strong><p>设置 Cat Codex 完成后何时提醒你</p></div><span className="select-like">仅在未聚焦时⌄</span></div><div className="setting-row"><div><strong>启用权限通知</strong><p>在需要通知权限时显示提醒</p></div><Toggle on label="启用权限通知" /></div><div className="setting-row"><div><strong>启用问题通知</strong><p>需要输入才能继续时显示提醒</p></div><Toggle on label="启用问题通知" /></div></div></section>
}

type InspectorData = { files: string[]; diff: string; output: string }

function HomeInspector({ activeTab, setActiveTab, language, onClose, data }: { activeTab: 'files' | 'diff' | 'output' | 'plugins'; setActiveTab: (tab: 'files' | 'diff' | 'output' | 'plugins') => void; language: 'zh' | 'en'; onClose: () => void; data: InspectorData }) {
  const label = (zh: string, en: string) => language === 'zh' ? zh : en
  const files = data.files.length ? data.files : ['App.tsx', 'styles.css']
  return <aside className="chat-home-inspector"><div className="chat-home-inspector-head"><div className="chat-home-inspector-context"><span className="context-dot" /> <span>{label('Cat Codex', 'Cat Codex')}</span><span className="chat-home-inspector-chip">{label('当前回合', 'Last turn')} <Icon name="chevron" /></span></div><button className="chat-rail-button" onClick={onClose} aria-label={label('关闭右侧面板', 'Close inspector')}><Icon name="split" /></button></div><div className="chat-home-inspector-tabs">{(['files', 'diff', 'output', 'plugins'] as const).map((tab) => <button key={tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'files' ? label('文件', 'Files') : tab === 'diff' ? label('差异', 'Diff') : tab === 'output' ? label('输出', 'Output') : label('插件', 'Plugins')}</button>)}</div>{activeTab === 'files' ? <div className="chat-home-inspector-content"><div className="chat-home-inspector-summary"><Icon name="file" /><strong>{label('本轮修改', 'This turn')}</strong><span className="diff-add">+{data.files.length || 5}</span><span className="diff-remove">−0</span></div>{files.map((file) => <button className="chat-home-code-file active" key={file} onClick={() => setActiveTab('diff')}><Icon name="file" /><span>{file}</span></button>)}<p className="chat-home-inspector-empty">{label('点击文件查看代码变更。', 'Select a file to inspect its code changes.')}</p></div> : activeTab === 'diff' ? <div className="chat-home-inspector-content"><div className="chat-home-inspector-summary"><Icon name="file" /><strong>{label('聚合差异', 'Aggregate diff')}</strong></div><pre className="chat-home-code-preview"><code>{data.diff || label('回合产生差异后会显示在这里。', 'The aggregate diff will appear here when a turn changes files.')}</code></pre><button className="outline-button chat-home-inspector-retry" onClick={() => setActiveTab('files')}>{label('返回文件列表', 'Back to files')}</button></div> : <div className="chat-home-inspector-content"><div className="chat-home-inspector-summary"><Icon name={activeTab === 'output' ? 'terminal' : 'puzzle'} /><strong>{activeTab === 'output' ? label('输出', 'Output') : label('插件', 'Plugins')}</strong></div><pre className="chat-home-code-preview">{activeTab === 'output' ? data.output || label('运行后，命令输出会显示在这里。', 'Command output will appear here after a run.') : label('当前工作区还没有启用插件。', 'No plugins are enabled in this workspace yet.')}</pre></div>}</aside>
}

export function App() {
  const [events, setEvents] = useState(initialEvents)
  const [input, setInput] = useState('')
  const [activeTab, setActiveTab] = useState<'files' | 'diff' | 'output' | 'plugins'>('files')
  const [notice, setNotice] = useState('')
  const [model, setModel] = useState('gpt-5.6-terra')
  const [activeView, setActiveView] = useState<AppView>('home')
  const [settingsReturnView, setSettingsReturnView] = useState<AppView>('home')
  const [settingsSection, setSettingsSection] = useState<SettingsSection>('general')
  const [providerDialogOpen, setProviderDialogOpen] = useState(false)
  const [providerPreset, setProviderPreset] = useState<ProviderId>('openai')
  const [providerEntries, setProviderEntries] = useState<ProviderEntry[]>(readProviderEntries)
  const [providerForm, setProviderForm] = useState<ProviderForm>({ name: '', note: '', baseUrl: '', apiFormat: 'OpenAI Responses', credentialEnv: '', model: '', apiKey: '', toolSearch: false, disableBeta: false, imageGeneration: false, settingsJson: '{\n  "model": ""\n}' })
  const [settingsSearch, setSettingsSearch] = useState('')
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const [homeInspectorOpen, setHomeInspectorOpen] = useState(false)
  const [inspectorData, setInspectorData] = useState<InspectorData>({ files: [], diff: '', output: '' })
  const [approvalRequest, setApprovalRequest] = useState<JsonRpcServerRequest | null>(null)
  const [language, setLanguage] = useState<'zh' | 'en'>(() => readStored<'zh' | 'en'>('cat-codex-language', 'zh'))
  const [customInstructions, setCustomInstructions] = useState('')
  const [memoryEnabled, setMemoryEnabled] = useState(false)
  const [theme, setTheme] = useState<'system' | 'light' | 'dark'>(() => readStored<'system' | 'light' | 'dark'>('cat-codex-theme', 'dark'))
  const textFor = (zh: string, en: string) => language === 'zh' ? zh : en
  const visibleSessions = sessions.map((session, index) => language === 'zh' ? { ...session, ...sessionCopy[index] } : session)
  const visibleEvent = (event: AgentEvent) => language === 'zh' && eventCopy[event.title] ? { ...event, ...eventCopy[event.title] } : event
  useEffect(() => writeStored('cat-codex-language', language), [language])
  useEffect(() => writeStored('cat-codex-theme', theme), [theme])
  useEffect(() => writeStored('cat-codex-provider-entries', providerEntries), [providerEntries])
  useEffect(() => {
    const copy: Record<string, string> = language === 'zh' ? { Settings: '设置', 'Back to home': '返回主页', 'Back to workspace': '返回工作区', WORKSPACE: '工作区', PERSONAL: '个人', CODING: '编码', SAFETY: '安全', ACCOUNT: '账户', TOOLS: '工具', 'CURRENT CONFIGURATION': '当前配置', Language: '语言', 'Interface and assistant response language': '界面与助手回复语言', 'Signed-in account': '已登录账户', 'Workspace sync': '工作区同步', 'Identity used by the active provider': '当前服务商使用的身份', 'Sync settings and sessions across devices': '跨设备同步设置和会话', 'App Server': '应用服务器', 'Connection used for sessions and streamed events': '用于会话和事件流的连接', Startup: '启动', 'Open the last workspace when the app launches': '应用启动时打开上次工作区', 'Not connected': '未连接', 'New chat': '新对话', Home: '主页', Projects: '项目', Plugins: '插件', Recent: '最近', 'Account & settings': '账户与设置', 'Local-first · not connected': '本地优先 · 未连接', 'Native shell features are off': '原生外壳功能已关闭', 'Add context': '添加上下文', Files: '文件', Model: '模型', 'Choose a project': '选择项目', 'API CONNECTIONS': 'API 连接', 'Service providers': '服务商', 'Add provider': '添加服务商', 'Not configured': '未配置', 'Coming soon': '即将推出', Edit: '编辑', 'CODING / PROVIDERS': '编码 / 服务商', Close: '关闭', 'Provider name': '服务商名称', 'Base URL': '基础地址', 'Credential environment variable': '凭据环境变量', 'Default model': '默认模型', 'Raw secrets are never stored in the web UI.': '原始密钥不会存储在网页界面中。', Cancel: '取消', 'Cat Codex can use your connected providers, tools, and plugins when they are configured.': '配置后，Cat Codex 可以使用已连接的服务商、工具和插件。' } : { 设置: 'Settings', 返回主页: 'Back to home', 返回工作区: 'Back to workspace', 工作区: 'WORKSPACE', 个人: 'PERSONAL', 编码: 'CODING', 安全: 'SAFETY', 账户: 'ACCOUNT', 工具: 'TOOLS', 当前配置: 'CURRENT CONFIGURATION', 语言: 'Language', '界面与助手回复语言': 'Interface and assistant response language', '已登录账户': 'Signed-in account', 工作区同步: 'Workspace sync', 未连接: 'Not connected', 新对话: 'New chat', 主页: 'Home', 项目: 'Projects', 插件: 'Plugins', 最近: 'Recent', '账户与设置': 'Account & settings', '本地优先 · 未连接': 'Local-first · not connected', '原生外壳功能已关闭': 'Native shell features are off', 添加上下文: 'Add context', 文件: 'Files', 模型: 'Model', 选择项目: 'Choose a project', '配置后，Cat Codex 可以使用已连接的服务商、工具和插件。': 'Cat Codex can use your connected providers, tools, and plugins when they are configured.', 'API 连接': 'API CONNECTIONS', 服务商: 'Service providers', 添加服务商: 'Add provider', 未配置: 'Not configured', 即将推出: 'Coming soon', 编辑: 'Edit', '编码 / 服务商': 'CODING / PROVIDERS', 关闭: 'Close', 服务商名称: 'Provider name', 基础地址: 'Base URL', 凭据环境变量: 'Credential environment variable', 默认模型: 'Default model', '原始密钥不会存储在网页界面中。': 'Raw secrets are never stored in the web UI.', 取消: 'Cancel' }
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
    const nodes: Text[] = []; let node: Node | null
    while ((node = walker.nextNode())) nodes.push(node as Text)
    nodes.forEach((text) => { const value = text.nodeValue?.trim(); if (value && copy[value]) text.nodeValue = text.nodeValue!.replace(value, copy[value]) })
  }, [language, settingsSection, activeView, providerDialogOpen])
  const [clientState, setClientState] = useState<'disconnected' | 'connecting' | 'ready' | 'error'>('disconnected')
  const nativeShell = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
  const client = useMemo(() => new CodexAppServerClient(nativeShell ? new TauriTransport() : new UnavailableTransport()), [nativeShell])
  const initialized = useRef(false)
  const threadId = useRef<string | null>(null)
  useEffect(() => {
    const unsubscribeState = client.onStateChange(setClientState)
    const unsubscribeEvents = client.subscribe((message) => {
      if (!('method' in message)) return
      const params = message.params as Record<string, unknown> | undefined
      if (message.method === 'turn/completed') setNotice('回合已完成。')
      if (message.method === 'turn/diff/updated' && typeof params?.diff === 'string') { setInspectorData((current) => ({ ...current, diff: params.diff as string })); setHomeInspectorOpen(true); setActiveTab('diff') }
      if (message.method === 'item/commandExecution/outputDelta' && typeof params?.delta === 'string') setInspectorData((current) => ({ ...current, output: `${current.output}${params.delta as string}` }))
      if (message.method === 'item/started' || message.method === 'item/completed') {
        const item = params?.item as Record<string, unknown> | undefined
        const file = typeof item?.filePath === 'string' ? item.filePath : typeof item?.path === 'string' ? item.path : undefined
        if (file) setInspectorData((current) => ({ ...current, files: current.files.includes(file) ? current.files : [...current.files, file] }))
      }
      const kind: EventKind = message.method.includes('file') ? 'file' : message.method.includes('command') ? 'tool' : 'notice'
      const event: AgentEvent = { time: new Date().toLocaleTimeString('zh-CN', { hour12: false }), kind, title: message.method, detail: typeof params?.delta === 'string' ? params.delta as string : 'App Server event received', tone: 'muted' }
      setEvents((current) => [event, ...current].slice(0, 30))
    })
    const unsubscribeRequests = client.onServerRequest((request) => {
      if (request.method === 'item/fileChange/requestApproval' || request.method === 'item/commandExecution/requestApproval') { setApprovalRequest(request); setHomeInspectorOpen(true) }
    })
    return () => { unsubscribeState(); unsubscribeEvents(); unsubscribeRequests(); client.dispose() }
  }, [client])
  const currentProvider = providers.find((provider) => provider.id === 'openai')!

  async function submit() {
    const trimmed = input.trim()
    if (!trimmed) return
    if (!nativeShell) {
      setNotice('未发送：Codex App Server 尚未连接。配置本地 app-server 后再发送。')
      setEvents((current) => [{ time: new Date().toLocaleTimeString('zh-CN', { hour12: false }), kind: 'notice', title: 'Request held', detail: 'Transport unavailable · no request sent', tone: 'active' }, ...current])
      return
    }
    try {
      if (!initialized.current) { await client.initialize({ name: 'cat-codex', title: 'Cat Codex', version: '0.1.0' }); initialized.current = true }
      if (!threadId.current) { const result = await client.startThread({ model, cwd: undefined }); threadId.current = result.thread.id }
      await client.startTurn({ threadId: threadId.current, input: [{ type: 'text', text: trimmed }], model })
      setInput('')
    } catch (error) { setNotice(`发送失败：${error instanceof Error ? error.message : String(error)}`) }
  }

  function openSettings(section: SettingsSection = 'general') {
    if (activeView !== 'settings') setSettingsReturnView(activeView)
    setSettingsSection(section)
    setActiveView('settings')
  }

  function closeSettings() {
    setActiveView(settingsReturnView)
  }

  function selectProviderPreset(id: ProviderId) {
    const provider = providerEntries.find((entry) => entry.id === id)
    const fallback = providers.find((entry) => entry.id === id)
    setProviderPreset(id)
    const display = providerDisplayCopy[id]
    setProviderForm({ name: display?.name ?? provider?.name ?? fallback?.name ?? '', note: display?.note ?? '', baseUrl: provider?.baseUrl ?? display?.baseUrl ?? '', apiFormat: display?.apiFormat ?? 'OpenAI Responses', credentialEnv: provider?.credentialEnv ?? display?.credentialEnv ?? '', model: provider?.models[0] ?? fallback?.models[0] ?? '', apiKey: '', toolSearch: false, disableBeta: false, imageGeneration: false, settingsJson: `{\n  "model": "${provider?.models[0] ?? fallback?.models[0] ?? ''}"\n}` })
  }

  function openProviderDialog(id: ProviderId = providerPreset) {
    selectProviderPreset(id)
    setProviderDialogOpen(true)
  }

  function saveProvider(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const name = providerForm.name.trim()
    const modelName = providerForm.model.trim()
    if (!name || !modelName) {
      setNotice(language === 'zh' ? '请填写服务商名称和默认模型。' : 'Enter a provider name and default model.')
      return
    }
    setProviderEntries((current) => current.map((entry) => entry.id === providerPreset ? { ...entry, name, models: [modelName, ...entry.models.filter((item) => item !== modelName)], baseUrl: providerForm.baseUrl.trim(), credentialEnv: providerForm.credentialEnv.trim(), configured: true } : entry))
    setNotice(language === 'zh' ? '服务商配置已保存（密钥仍由原生外壳管理）。' : 'Provider configuration saved; secrets remain in the native shell.')
    setProviderDialogOpen(false)
  }

  const providerKeyUrl = providerKeyLinks[providerPreset] ?? ''
  const activeSettings = { ...settingsMeta[settingsSection], title: language === 'zh' ? ({ general: '常规', import: '导入', profile: '个人资料', appearance: '外观', models: '模型与服务商', providers: '服务商', hooks: '钩子', voice: '语音', shortcuts: '键盘快捷键', permissions: '权限', usage: '使用情况和计费', account: '账户', computer: '电脑操控', history: '计算机历史记录', snapshots: '应用快照', plugins: '插件', browser: '浏览器', configuration: '配置', personalization: '个性化', companion: '智能伙伴', connections: '连接', git: 'Git', environment: '环境', worktrees: '工作树', archived: '已归档的聊天' } as Record<SettingsSection, string>)[settingsSection] : settingsMeta[settingsSection].title, description: language === 'zh' ? '管理 Cat Codex 工作台设置。' : settingsMeta[settingsSection].description }
  const localizedEyebrow = settingsSection === 'git' || settingsSection === 'worktrees' ? '' : language === 'zh' ? ({ WORKSPACE: '工作区', PERSONAL: '个人', INPUT: '输入', CODING: '编码', SAFETY: '安全', ACCOUNT: '账户', TOOLS: '工具', EXTENSIONS: '扩展', PROVIDERS: '服务商', ARCHIVED: '已归档' } as Record<string, string>)[activeSettings.eyebrow] ?? activeSettings.eyebrow : activeSettings.eyebrow
  const localizedDescription = settingsSection === 'git' || settingsSection === 'worktrees' ? '' : language === 'zh' ? ({ general: '', import: '将其他 AI 应用的设置、项目和聊天导入 Cat Codex', profile: '', appearance: '', models: '选择默认模型，并在安装适配器后连接其他服务商。', providers: '管理 API 服务商以访问模型。', hooks: '通过配置和已启用的插件管理生命周期钩子。 了解更多', voice: '管理语音聊天、听写和屏幕上下文。', shortcuts: '管理工作区快捷键。', permissions: '查看 Cat Codex 修改文件、运行命令或使用网络前的权限边界。', usage: '如需查看发票、更改付款方式或进行其他操作，请前往网页版设置', account: '管理 Cat Codex 工作台设置。', computer: '管理 Cat Codex 如何使用你电脑上的其他应用程序', history: '', snapshots: '', plugins: '管理插件、技能和 MCP。', browser: '管理内置浏览器。可在计算机使用设置中设置浏览器扩展程序', configuration: '配置新聊天的权限、网页访问和智能体回复。', personalization: '', companion: '', connections: '管理工作区连接。', git: '配置 Git 集成。', environment: '本地环境会告诉 Cat Codex 如何为项目设置工作树。了解更多', worktrees: '', archived: '' } as Partial<Record<SettingsSection, string>>)[settingsSection] ?? activeSettings.description : activeSettings.description
  const settingsGroups = [...new Set(settingsSections.map((section) => section.group))]
  const settingsBackLabel = language === 'zh' ? '返回应用' : 'Back to app'
  const localizedSectionLabel = (section: typeof settingsSections[number]) => language === 'zh' ? (({ general: '常规', import: '导入', profile: '个人资料', appearance: '外观', models: '模型与服务商', providers: '服务商', language: '语言', hooks: '钩子', voice: '语音', shortcuts: '键盘快捷键', permissions: '权限', usage: '使用情况和计费', account: '账户', computer: '电脑操控', history: '计算机历史记录', snapshots: '应用快照', plugins: '插件', browser: '浏览器', configuration: '配置', personalization: '个性化', companion: '智能伙伴', connections: '连接', git: 'Git', environment: '环境', worktrees: 'Worktrees', archived: '已归档的聊天' } as unknown as Record<SettingsSection, string>)[section.id] ?? section.label) : section.label
  const filteredSettingsGroups = settingsGroups.map((group) => ({ group, sections: settingsSections.filter((section) => section.group === group && `${localizedSectionLabel(section)} ${section.label}`.toLocaleLowerCase().includes(settingsSearch.trim().toLocaleLowerCase())) })).filter((group) => group.sections.length > 0)
  const localizedTitle = language === 'zh' ? (({ general: '常规', import: '导入', profile: '个人资料', appearance: '外观', models: '模型与服务商', providers: '服务商', hooks: '钩子', voice: '语音', shortcuts: '键盘快捷键', permissions: '权限', usage: '使用情况和计费', account: '账户', computer: '电脑操控', history: '计算机历史记录', snapshots: '应用快照', plugins: '插件', browser: '浏览器', configuration: '配置', personalization: '个性化', companion: '智能伙伴', connections: '连接', git: 'Git', environment: '环境', worktrees: 'Worktrees', archived: '已归档的聊天' } as unknown as Record<SettingsSection, string>)[settingsSection] ?? activeSettings.title) : activeSettings.title
  const localizedRows = language === 'zh' ? (({
    models: [
      { label: '默认模型', detail: '新会话使用的默认模型', value: 'gpt-5.6-terra' },
      { label: '当前服务商', detail: '默认模型使用的服务商适配器', value: 'OpenAI / Codex' },
      { label: '其他服务商', detail: 'DeepSeek、Claude、Gemini、本地及兼容 API', value: '未连接' },
    ],
    providers: [
      { label: '已配置服务商', detail: '可供模型选择器使用的服务商', value: '1 个可用' },
      { label: '默认服务商', detail: '新会话使用的服务商', value: 'OpenAI / Codex' },
      { label: '密钥存储', detail: 'API 密钥和 OAuth 令牌', value: '仅原生外壳' },
    ],
    hooks: [
      { label: '会话钩子', detail: '在 Codex 回合前后运行', value: '未配置' },
      { label: '更改防护', detail: '应用前验证文件更改', value: '关闭' },
      { label: '密钥边界', detail: '钩子命令在原生外壳中运行', value: '仅本地' },
    ],
    permissions: [
      { label: '文件更改', detail: '编辑前需要批准', value: '更改前询问' },
      { label: '网络访问', detail: '来自原生外壳的出站请求', value: '关闭' },
      { label: '应用服务器', detail: '原生传输端点', value: '未连接' },
    ],
    connections: [{ label: '连接', detail: '外部开发连接', value: '未配置' }],
    git: [{ label: 'Git 状态', detail: '仓库集成', value: '就绪' }],
    environment: [{ label: '环境', detail: '运行时环境', value: '本地' }],
    worktrees: [{ label: '工作树', detail: '工作树位置', value: '无' }],
    archived: [{ label: '已归档的聊天', detail: '移出最近记录的对话', value: '0 个聊天' }],
  } as Partial<Record<SettingsSection, Array<{ label: string; detail: string; value: string }>>>)[settingsSection] ?? activeSettings.rows) : activeSettings.rows
  const settingIcon = (id: SettingsSection): Parameters<typeof Icon>[0]['name'] => (({ general: 'settings', import: 'file', profile: 'user', appearance: 'sun', models: 'chat', providers: 'terminal', language: 'browser', hooks: 'hook', voice: 'mic', shortcuts: 'keyboard', permissions: 'lock', usage: 'chart', account: 'user', computer: 'monitor', history: 'history', snapshots: 'camera', plugins: 'puzzle', browser: 'browser', configuration: 'sliders', personalization: 'bot', companion: 'spark', connections: 'link', git: 'git', environment: 'terminal', worktrees: 'folder', archived: 'archive' } as unknown as Record<SettingsSection, Parameters<typeof Icon>[0]['name']>)[id] ?? 'settings')

  activeSettings.title = localizedTitle

  return (
    <div className={`app-shell ${theme === 'light' ? 'light-theme' : ''}`}>
      {providerDialogOpen && <ProviderDialog providerEntries={providerEntries} providerPreset={providerPreset} providerForm={providerForm} providerKeyUrl={providerKeyUrl} language={language} setProviderPreset={selectProviderPreset} setProviderForm={setProviderForm} onClose={() => setProviderDialogOpen(false)} onSave={saveProvider} onTest={() => setNotice(language === 'zh' ? '测试连接为本地预览，真实请求需要原生传输。' : 'Connection test is a local preview; native transport is required for a real request.')} />}
      {activeView !== 'home' && <header className="topbar">
        <div className="brand-lockup"><div className="brand-mark"><span>◒</span></div><div><strong>cat codex</strong><small>agent workbench</small></div></div>
        <div className="topbar-context"><span className="context-dot" /> {activeView === 'settings' ? (language === 'zh' ? '设置' : 'Settings') : <>{language === 'zh' ? '新建项目' : 'New project'} <span className="slash">/</span> {language === 'zh' ? '本地' : 'local'}</>}</div>
        <div className="topbar-actions"><button className="icon-button" aria-label="Toggle panels"><Icon name="panel" /></button><button className={`icon-button ${activeView === 'settings' ? 'active' : ''}`} aria-label="Settings" onClick={() => openSettings()}><Icon name="settings" /></button><div className="avatar">NG</div></div>
      </header>}

      {activeView === 'home' ? <section className={`chat-home-shell ${homeInspectorOpen ? 'with-inspector' : ''}`} aria-label={textFor('Cat Codex 主页', 'Cat Codex home')}>
        <aside className="chat-sidebar">
          <div className="chat-sidebar-utility"><button className="chat-rail-button" aria-label={textFor('折叠侧栏', 'Collapse sidebar')}><Icon name="panel" /></button><button className="chat-rail-button" aria-label={textFor('后退', 'Back')}><Icon name="back" /></button><button className="chat-rail-button" aria-label={textFor('前进', 'Forward')}><Icon name="forward" /></button></div>
          <div className="chat-brand-row"><button className="chat-brand" onClick={() => setActiveView('home')} aria-label={textFor('Cat Codex 主页', 'Cat Codex home')}><span className="chat-brand-mark">◒</span><span>cat codex</span><span className="chat-brand-caret">⌄</span></button><div className="chat-brand-actions"><button className="chat-rail-button" aria-label={textFor('搜索对话', 'Search chats')}><Icon name="search" /></button><button className="chat-rail-button" aria-label={textFor('通知', 'Notifications')}><Icon name="bell" /></button></div></div>
          <div className="chat-sidebar-actions"><button className="chat-new-button" onClick={() => { setInput(''); setNotice(''); setActiveView('home') }}><Icon name="plus" /> {textFor('新对话', 'New chat')}</button></div>
          <nav className="chat-primary-nav" aria-label={textFor('主导航', 'Primary')}><button className="chat-nav-item selected"><Icon name="chat" /> {textFor('主页', 'Home')}</button><button className="chat-nav-item" onClick={() => setActiveView('workspace')}><Icon name="folder" /> {textFor('项目', 'Projects')} <span>3</span></button><button className="chat-nav-item" onClick={() => openSettings('plugins')}><Icon name="spark" /> {textFor('插件', 'Plugins')} <span>0</span></button></nav>
          <div className="chat-history"><p className="chat-nav-label">{textFor('最近', 'Recent')}</p>{visibleSessions.map((session) => <button key={session.name} className="chat-history-item" onClick={() => setActiveView('workspace')}><Icon name="chat" /><span>{session.name}</span></button>)}</div>
          <div className="chat-sidebar-footer">
            {accountMenuOpen && <div className="chat-account-menu" role="menu">
              <div className="chat-account-menu-head"><span className="avatar">NG</span><div><strong>NG</strong><small>{textFor('本地账户', 'Local account')}</small></div></div>
              <button type="button" role="menuitem" onClick={() => { setAccountMenuOpen(false); openSettings('usage') }}><Icon name="chart" /> {textFor('剩余用量', 'Usage')}</button>
              <button type="button" role="menuitem" onClick={() => { setAccountMenuOpen(false); openSettings('companion') }}><Icon name="spark" /> {textFor('隐藏宠物', 'Hide companion')}</button>
              <button type="button" role="menuitem" onClick={() => { setAccountMenuOpen(false); setNotice(textFor('邀请同事功能将在账户连接后开放。', 'Inviting teammates will be available after account connection.')) }}><Icon name="link" /> {textFor('邀请同事', 'Invite teammates')}</button>
              <div className="chat-account-menu-divider" />
              <button type="button" role="menuitem" onClick={() => { setAccountMenuOpen(false); openSettings('account') }}><Icon name="settings" /> {textFor('设置', 'Settings')}</button>
              <button type="button" role="menuitem" onClick={() => { setAccountMenuOpen(false); setNotice(textFor('退出登录需要账户连接。', 'Sign out requires an account connection.')) }}><Icon name="logout" /> {textFor('退出登录', 'Sign out')}</button>
            </div>}
            <button type="button" className={`chat-account-button ${accountMenuOpen ? 'open' : ''}`} aria-haspopup="menu" aria-expanded={accountMenuOpen} onClick={() => setAccountMenuOpen((open) => !open)}><span className="avatar">NG</span><span className="chat-account-copy"><strong>NG</strong><small>{textFor('账户与设置', 'Account & settings')}</small></span><Icon name="chevron" /></button>
          </div>
        </aside>
        <main className="chat-home-main"><header className="chat-home-header"><button className="chat-model-button" onClick={() => openSettings('models')}><Icon name="folder" /><span>Cat Codex</span><span className="chat-model-caret">⌄</span></button><div className="chat-home-actions"><button className="chat-rail-button" aria-label={textFor('调整显示', 'Adjust display')} onClick={() => setNotice(textFor('显示选项已打开。', 'Display options opened.'))}><Icon name="sliders" /></button><button className="chat-rail-button" aria-label={textFor('收起面板', 'Close inspector')} onClick={() => setHomeInspectorOpen(false)}><Icon name="minimize" /></button><button className="chat-rail-button" aria-label={textFor('展开右侧面板', 'Open inspector')} onClick={() => setHomeInspectorOpen(true)}><Icon name="split" /></button></div></header><div className="chat-home-center"><div className="chat-greeting"><div className="welcome-icon"><span>◒</span></div><h1>{textFor('我们今天要做什么？', 'What should we work on?')}</h1><p>{textFor('让 Cat Codex 检查、规划或修改工作区。', 'Ask Cat Codex to inspect, plan, or change a workspace.')}</p></div><div className="chat-home-composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) submit() }} placeholder={textFor('处理任何事务', 'Work on anything')} rows={3} aria-label={textFor('向 Cat Codex 提问', 'Ask Cat Codex')} /><div className="chat-home-composer-footer"><div className="chat-home-tools"><button className="composer-tool"><Icon name="plus" /> {textFor('添加上下文', 'Add context')}</button><button className="composer-tool" onClick={() => setActiveView('workspace')}><Icon name="folder" /> {textFor('文件', 'Files')}</button></div><div className="chat-home-send"><label className="chat-home-model"><span>{textFor('模型', 'Model')}</span><select value={model} onChange={(event) => setModel(event.target.value)} aria-label={textFor('主页模型', 'Home model')}>{currentProvider.models.map((item) => <option key={item}>{item}</option>)}</select><Icon name="chevron" /></label><button className="send-button" onClick={submit} aria-label={textFor('发送消息', 'Send message')}><Icon name="send" /></button></div></div></div><button className="chat-project-picker" onClick={() => setActiveView('workspace')}><Icon name="folder" /><span>{textFor('选择项目', 'Choose a project')}</span><Icon name="chevron" /></button>{notice && <div className="chat-home-notice" role="status">{notice}<button onClick={() => setNotice('')}>{textFor('关闭', 'Dismiss')}</button></div>}</div><p className="chat-home-footnote">{textFor('配置完成后，Cat Codex 可以使用已连接的服务商、工具和插件。', 'Cat Codex can use your connected providers, tools, and plugins when they are configured.')}</p></main>
        {homeInspectorOpen && <HomeInspector activeTab={activeTab} setActiveTab={setActiveTab} language={language} data={inspectorData} onClose={() => setHomeInspectorOpen(false)} />}
        {approvalRequest && <div className="approval-banner" role="alert"><strong>{approvalRequest.method === 'item/fileChange/requestApproval' ? textFor('请求批准文件更改', 'File change approval requested') : textFor('请求批准执行命令', 'Command approval requested')}</strong><span>{String((approvalRequest.params as Record<string, unknown>)?.reason ?? (approvalRequest.params as Record<string, unknown>)?.command ?? '')}</span><button onClick={() => { client.respond(approvalRequest.id, { decision: 'decline' }); setApprovalRequest(null) }}>{textFor('拒绝', 'Decline')}</button><button className="primary-action" onClick={() => { client.respond(approvalRequest.id, { decision: 'accept' }); setApprovalRequest(null) }}>{textFor('批准', 'Approve')}</button></div>}
      </section> : activeView === 'workspace' ? <div className="workspace-grid">
        <aside className="sidebar">
          <div className="sidebar-actions"><button className="new-button" onClick={() => setActiveView('home')}><Icon name="plus" /> {textFor('新会话', 'New session')}</button><button className="icon-button subtle" aria-label={textFor('搜索会话', 'Search sessions')}><Icon name="search" /></button></div>
          <div className="sidebar-heading"><span>{textFor('项目', 'Projects')}</span><button className="tiny-button" aria-label={textFor('展开项目', 'Expand projects')}><Icon name="chevron" /></button></div>
          <div className="project-row active"><span className="project-glyph">N</span><span className="project-copy"><strong>{textFor('新建项目', 'New project')}</strong><small>~/Documents/Codex</small></span><span className="project-count">3</span></div>
          <div className="sidebar-heading session-heading"><span>{textFor('会话', 'Sessions')}</span><span className="session-count">3</span></div>
          <nav className="session-list" aria-label={textFor('会话', 'Sessions')}>{visibleSessions.map((session) => <button key={session.name} className={`session-row ${session.selected ? 'selected' : ''}`}><span className="session-icon"><Icon name="chat" /></span><span className="session-copy"><strong>{session.name}</strong><small>{session.subtitle}</small></span><time>{session.time}</time></button>)}</nav>
          <div className="sidebar-bottom"><button className="sidebar-link" onClick={() => setActiveTab('plugins')}><Icon name="spark" /> {textFor('插件注册表', 'Plugin registry')} <span className="sidebar-pill">0</span></button><button className="sidebar-link"><Icon name="folder" /> {textFor('打开文件夹', 'Open folder')}</button><button className="sidebar-link" onClick={() => openSettings()}><Icon name="settings" /> {textFor('偏好设置', 'Preferences')} <kbd>⌘ ,</kbd></button></div>
        </aside>

        <main className="conversation">
          <div className="conversation-header"><div><p className="eyebrow">{textFor('会话 · 001', 'SESSION · 001')}</p><h1>{textFor('Cat Codex 初次检查', 'Cat Codex first pass')}</h1></div><div className="header-tools"><button className="header-action" onClick={() => setNotice(textFor('分享链接将在连接账户后生成。', 'A share link will be available after account connection.'))}>{textFor('分享', 'Share')}</button><button className="header-action" onClick={() => setNotice(textFor('显示选项已打开。', 'Display options opened.'))}>{textFor('调整', 'Adjust')}</button><button className="icon-button subtle" aria-label={textFor('切换面板', 'Toggle panels')}><Icon name="panel" /></button><span className="local-chip"><span className="chip-dot" /> {textFor('本地工作区', 'Local workspace')}</span><button className="icon-button subtle" aria-label={textFor('更多会话操作', 'More session actions')} onClick={() => setNotice(textFor('会话操作菜单：置顶、重命名、复制、归档。', 'Session actions: pin, rename, copy, archive.'))}>•••</button></div></div>
          <div className="conversation-scroll">
            <section className="welcome-block"><div className="welcome-icon"><span>◒</span></div><div><h2>{textFor('准备好后就开始。', 'Ready when you are.')}</h2><p>{textFor('让 Cat Codex 检查、规划或修改这个工作区。每一步操作都会显示在事件流中。', 'Ask Cat Codex to inspect, plan, or change this workspace. Every action will appear in the event stream.')}</p></div></section>
            <section className="request-card"><div className="request-meta"><span className="request-avatar">NG</span><span>{textFor('你', 'You')}</span><time>{textFor('今天 09:40', 'Today, 09:40')}</time></div><p>先检查仓库规则和现状，搭一个可启动的 Cat Codex 工作台骨架。</p></section>
            <section className="agent-section"><div className="section-label"><span className="live-line" /> {textFor('智能体事件', 'Agent events')} <span className="event-count">{events.length}</span></div><div className="event-stream">{events.map((event, index) => { const visible = visibleEvent(event); return <div className={`event-row ${event.tone === 'active' ? 'event-active' : ''}`} key={`${event.time}-${index}`}><div className={`event-icon event-${event.kind}`}><Icon name={event.kind === 'thought' ? 'spark' : event.kind === 'tool' ? 'terminal' : event.kind === 'file' ? 'file' : 'lock'} /></div><div className="event-body"><div><strong>{visible.title}</strong>{event.tone === 'active' && <span className="working-badge">{textFor('等待中', 'waiting')}</span>}</div><p>{visible.detail}</p></div><time>{event.time}</time></div> })}</div></section>
            <section className="connection-note"><div className="note-icon"><Icon name="lock" /></div><div><strong>{textFor('App Server 连接已关闭', 'App Server connection is off')}</strong><p>{textFor('Cat Codex 采用本地优先模式。请在原生外壳中设置 App Server 端点以启用对话。', 'Cat Codex is local-first. Set an app-server endpoint in the native shell to enable conversations.')}</p></div><button onClick={() => setNotice(textFor('连接配置将在 Tauri/native transport 接入阶段开放。', 'Connection settings will be available after the Tauri/native transport is integrated.'))}>{textFor('了解方法', 'Learn how')}</button></section>
          </div>
          <div className="composer-wrap"><div className="composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) submit() }} placeholder={textFor('询问有关此工作区的任何问题…', 'Ask Cat Codex anything about this workspace…')} rows={2} /><div className="composer-footer"><div className="composer-tools"><button className="composer-tool"><Icon name="plus" /> {textFor('添加上下文', 'Add context')}</button><button className="composer-tool"><Icon name="folder" /> {textFor('文件', 'Files')}</button><span className="shortcut-hint">{textFor('⌘↵ 发送', '⌘↵ to send')}</span></div><button className="send-button" onClick={submit} aria-label={textFor('发送消息', 'Send message')}><Icon name="send" /></button></div></div>{notice && <div className="composer-notice" role="status">{notice}<button onClick={() => setNotice('')}>{textFor('关闭', 'Dismiss')}</button></div>}</div>
        </main>

        <aside className="inspector">
          <div className="inspector-tabs" role="tablist">{(['files', 'diff', 'output', 'plugins'] as const).map((tab) => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab === 'files' ? textFor('文件', 'Files') : tab === 'diff' ? textFor('差异', 'Diff') : tab === 'output' ? textFor('输出', 'Output') : textFor('插件', 'Plugins')}{tab === 'diff' && <span className="tab-count">2</span>}{tab === 'plugins' && <span className="tab-count muted-count">0</span>}</button>)}</div>
          {activeTab === 'files' && <div className="inspector-content"><div className="tree-root"><Icon name="folder" /><strong>{textFor('新建项目', 'New project')}</strong><span>{textFor('14 个文件', '14 files')}</span></div><div className="file-tree"><div className="tree-row"><Icon name="folder" /><span>apps</span><Icon name="chevron" /></div><div className="tree-row indent"><Icon name="folder" /><span>cat-codex</span><span className="new-marker">{textFor('新', 'new')}</span></div><div className="tree-row indent"><Icon name="folder" /><span>src/lib/codex</span><Icon name="chevron" /></div><div className="tree-row"><Icon name="file" /><span>README.md</span></div><div className="tree-row"><Icon name="file" /><span>package.json</span></div><div className="tree-row"><Icon name="file" /><span>tauri.conf.json</span></div></div><div className="inspector-section"><div className="inspector-label">{textFor('工作区', 'WORKSPACE')}</div><div className="stat-line"><span>{textFor('分支', 'Branch')}</span><strong><Icon name="git" /> main</strong></div><div className="stat-line"><span>{textFor('上次索引', 'Last indexed')}</span><strong>{textFor('刚刚', 'just now')}</strong></div></div></div>}
          {activeTab === 'diff' && <div className="inspector-content"><div className="diff-summary"><span className="diff-add">+ 318</span><span className="diff-remove">− 0</span><span className="diff-files">{textFor('4 个文件', '4 files')}</span></div><pre className="diff-preview"><code><span className="code-muted">apps/cat-codex/</span>{'\n'}<span className="code-add">+ src/App.tsx</span>{'\n'}<span className="code-add">+ src/styles.css</span>{'\n'}<span className="code-add">+ src/lib/codex/client.ts</span>{'\n'}<span className="code-add">+ src/lib/providers.ts</span></code></pre><p className="empty-copy">{textFor('更改会保留在本地，直到你审查并应用。', 'Changes stay local until you review and apply them.')}</p></div>}
          {activeTab === 'output' && <div className="inspector-content output-panel"><div className="output-status"><span className="status-dot" /> {textFor('尚未运行', 'No run yet')}</div><p>{textFor('从原生外壳启动工作区检查后，命令输出会在这里持续显示。', 'Start the workspace check from the native shell to stream command output here.')}</p><button className="outline-button"><Icon name="terminal" /> {textFor('打开终端', 'Open terminal')}</button></div>}
          {activeTab === 'plugins' && <div className="inspector-content plugins-panel"><div className="plugin-header"><div><p className="eyebrow">{textFor('扩展点', 'EXTENSION POINTS')}</p><h3>{textFor('插件注册表', 'Plugin registry')}</h3></div><span className="plugin-count">{textFor(`已安装 ${installedPlugins.length} 个`, `${installedPlugins.length} installed`)}</span></div><p className="plugin-intro">{textFor('插件可以添加服务商、工具、MCP 服务器、技能、面板或工作流。此工作区暂未启用任何插件。', 'Plugins can add a provider, tool, MCP server, skill, panel, or workflow. Nothing is active in this workspace yet.')}</p><div className="plugin-list">{(['provider', 'tool', 'mcp', 'skill', 'panel', 'workflow'] as PluginExtension[]).map((extension) => <div className="plugin-slot" key={extension}><span className="slot-dot" /><span>{language === 'zh' ? ({ provider: '服务商', tool: '工具', mcp: 'MCP', skill: '技能', panel: '面板', workflow: '工作流' } as Record<PluginExtension, string>)[extension] : extensionLabels[extension]}</span><span className="slot-state">{textFor('未安装', 'Not installed')}</span></div>)}</div><button className="outline-button" onClick={() => setNotice(textFor('插件安装入口会在签名清单与权限审查完成后开放。', 'Plugin installation will open after manifest signing and permission review.'))}><Icon name="plus" /> {textFor('添加插件', 'Add plugin')}</button></div>}
          <div className="inspector-footer"><div className="footer-status"><span className={`status-dot ${clientState === 'ready' ? 'ready' : ''}`} /><span>{clientState === 'ready' ? textFor('已连接', 'Connected') : textFor('未连接', 'Not connected')}</span></div><label className="model-select"><span>{textFor('模型', 'Model')}</span><select value={model} onChange={(event) => setModel(event.target.value)}>{currentProvider.models.map((item) => <option key={item}>{item}</option>)}</select><Icon name="chevron" /></label><div className="permission-row"><Icon name="lock" /><span>{textFor('更改前询问', 'Ask before changes')}</span><button aria-label={textFor('更改权限', 'Change permissions')}>⌄</button></div></div>
        </aside>
      </div> : <section className="settings-shell" aria-label="Settings">
        <aside className="settings-nav">
          <div className="settings-nav-header"><button className="settings-return" onClick={closeSettings} aria-label={settingsBackLabel}><Icon name="chevron" /> {settingsBackLabel}</button></div>
          <label className="settings-search"><Icon name="search" /><input value={settingsSearch} onChange={(event) => setSettingsSearch(event.target.value)} aria-label={language === 'zh' ? '搜索设置' : 'Search settings'} placeholder={language === 'zh' ? '搜索设置' : 'Search settings'} /></label>
          <nav className="settings-section-list">{filteredSettingsGroups.map(({ group, sections }) => <div key={group}><p className="settings-group-label">{language === 'zh' ? ({ Personal: '个人', Integrations: '集成', Workspace: '工作区', Coding: '编码', Safety: '安全', Account: '账户', Tools: '工具', Archived: '已归档' } as Record<string, string>)[group] ?? group : group}</p>{sections.map((section) => <button key={section.id} className={`settings-nav-item ${settingsSection === section.id ? 'selected' : ''}`} onClick={() => setSettingsSection(section.id)}><Icon name={settingIcon(section.id)} />{localizedSectionLabel(section)}</button>)}</div>)}{filteredSettingsGroups.length === 0 && <p className="settings-search-empty">{language === 'zh' ? '未找到匹配设置' : 'No matching settings'}</p>}</nav>
          <div className="settings-nav-footer"><span className="status-dot" /> {language === 'zh' ? '原生外壳功能已关闭' : 'Native shell features are off'}</div>
        </aside>
          <main className="settings-content"><header className="settings-header"><div><p className="eyebrow">{localizedEyebrow}</p><h1>{activeSettings.title}</h1><p className={localizedDescription ? '' : 'settings-header-description-empty'}>{localizedDescription}</p></div></header>{notice && <div className="composer-notice settings-notice" role="status">{notice}<button type="button" onClick={() => setNotice('')}>{language === 'zh' ? '关闭' : 'Dismiss'}</button></div>}<div className="settings-scroll">{settingsSection === 'general' ? <GeneralPage setNotice={setNotice} language={language} /> : settingsSection === 'language' ? <LanguagePage language={language} setLanguage={setLanguage} /> : settingsSection === 'providers' ? <section className="provider-manager"><div className="provider-manager-head"><div><div className="settings-card-label">{language === 'zh' ? 'API 连接' : 'API CONNECTIONS'}</div><h2>{language === 'zh' ? '服务商' : 'Service providers'}</h2></div><button className="accent-button" onClick={() => openProviderDialog()}><Icon name="plus" /> {language === 'zh' ? '添加服务商' : 'Add provider'}</button></div><div className="provider-list">{providerEntries.map((provider) => <article className="provider-card" key={provider.id}><div className="provider-status-dot" data-status={provider.status} /><div className="provider-card-copy"><strong>{provider.name}</strong><p>{provider.shortName} · {provider.models[0]}</p></div><span className={`provider-badge ${provider.status}`}>{provider.configured ? (language === 'zh' ? '已保存' : 'Saved') : provider.status === 'not-configured' ? (language === 'zh' ? '未配置' : 'Not configured') : (language === 'zh' ? '即将推出' : 'Coming soon')}</span><button className="provider-edit" onClick={() => openProviderDialog(provider.id)}>{language === 'zh' ? '编辑' : 'Edit'}</button></article>)}</div></section> : settingsSection === 'personalization' ? <PersonalizationPage instructions={customInstructions} setInstructions={setCustomInstructions} memoryEnabled={memoryEnabled} setMemoryEnabled={setMemoryEnabled} setNotice={setNotice} /> : settingsSection === 'import' ? <ImportPage setNotice={setNotice} /> : settingsSection === 'profile' ? <ProfilePage setNotice={setNotice} /> : settingsSection === 'appearance' ? <AppearancePage setNotice={setNotice} theme={theme} setTheme={setTheme} /> : settingsSection === 'voice' ? <VoicePage setNotice={setNotice} /> : settingsSection === 'configuration' ? <ConfigurationPage setNotice={setNotice} /> : settingsSection === 'account' ? <AccountPage /> : settingsSection === 'companion' ? <CompanionPage setNotice={setNotice} /> : settingsSection === 'shortcuts' ? <ShortcutsPage setNotice={setNotice} /> : settingsSection === 'usage' ? <UsagePage setNotice={setNotice} /> : settingsSection === 'computer' ? <ComputerPage setNotice={setNotice} /> : settingsSection === 'history' ? <HistoryPage setNotice={setNotice} /> : settingsSection === 'snapshots' ? <SnapshotsPage setNotice={setNotice} /> : settingsSection === 'browser' ? <BrowserPage setNotice={setNotice} /> : settingsSection === 'hooks' ? <HooksPage setNotice={setNotice} /> : settingsSection === 'connections' ? <ConnectionsPage setNotice={setNotice} /> : settingsSection === 'git' ? <GitPage setNotice={setNotice} language={language} /> : settingsSection === 'environment' ? <EnvironmentPage setNotice={setNotice} language={language} /> : settingsSection === 'worktrees' ? <WorktreesPage setNotice={setNotice} language={language} /> : settingsSection === 'archived' ? <ArchivedPage setNotice={setNotice} language={language} /> : settingsSection === 'plugins' ? <PluginsPage setNotice={setNotice} /> : <section className="settings-card"><div className="settings-card-label">{language === 'zh' ? '当前配置' : 'CURRENT CONFIGURATION'}</div>{localizedRows.map((row) => <div className="setting-row" key={row.label}><div><strong>{row.label}</strong><p>{row.detail}</p></div><span className={`setting-value ${row.value.includes('未') || row.value.includes('关闭') || row.value === 'Unavailable' ? 'muted' : ''}`}>{row.value}</span></div>)}</section>}{(settingsSection === 'models' || settingsSection === 'permissions') && <section className="settings-footnote"><Icon name="lock" /><div><strong>{language === 'zh' ? '设置以本地优先' : 'Settings are local-first'}</strong><p>{language === 'zh' ? '需要原生外壳、服务商或外部账户的更改，会在边界连接前保持不可用。' : 'Changes that require the native shell, a provider, or an external account will stay unavailable until that boundary is connected.'}</p></div></section>}</div>{providerDialogOpen && <div className="provider-dialog-backdrop" role="presentation" onMouseDown={() => setProviderDialogOpen(false)}><form className="provider-dialog" onSubmit={saveProvider} onMouseDown={(event) => event.stopPropagation()}><div className="provider-dialog-head"><div><p className="eyebrow">{language === 'zh' ? '编码 / 服务商' : 'CODING / PROVIDERS'}</p><h2>{language === 'zh' ? '添加服务商' : 'Add provider'}</h2></div><button type="button" className="icon-button subtle" onClick={() => setProviderDialogOpen(false)} aria-label={language === 'zh' ? '关闭' : 'Close'}>×</button></div><div className="provider-presets">{providers.map((provider) => <button type="button" key={provider.id} className={providerPreset === provider.id ? 'selected' : ''} onClick={() => selectProviderPreset(provider.id)}>{provider.shortName}</button>)}</div><label>{language === 'zh' ? '服务商名称' : 'Provider name'}<input value={providerForm.name} onChange={(event) => setProviderForm((current) => ({ ...current, name: event.target.value }))} /></label><label>{language === 'zh' ? '基础地址' : 'Base URL'}<input value={providerForm.baseUrl} onChange={(event) => setProviderForm((current) => ({ ...current, baseUrl: event.target.value }))} placeholder="https://api.example.com/v1" /></label><label>{language === 'zh' ? '凭据环境变量' : 'Credential environment variable'}<input value={providerForm.credentialEnv} onChange={(event) => setProviderForm((current) => ({ ...current, credentialEnv: event.target.value }))} placeholder="OPENAI_API_KEY" /></label>{providerKeyUrl && <a className="provider-key-link" href={providerKeyUrl} target="_blank" rel="noreferrer">{language === 'zh' ? '获取 API 密钥 ↗' : 'Get API key ↗'}</a>}<label>{language === 'zh' ? '默认模型' : 'Default model'}<input value={providerForm.model} onChange={(event) => setProviderForm((current) => ({ ...current, model: event.target.value }))} /></label><p className="provider-dialog-note"><Icon name="lock" /> {language === 'zh' ? '原始密钥不会存储在网页界面中。' : 'Raw secrets are never stored in the web UI.'}</p><div className="provider-dialog-actions"><button type="button" className="outline-button" onClick={() => setProviderDialogOpen(false)}>{language === 'zh' ? '取消' : 'Cancel'}</button><button type="submit" className="accent-button">{language === 'zh' ? '保存服务商' : 'Save provider'}</button></div></form></div>}</main>
      </section>}
    </div>
  )
}
