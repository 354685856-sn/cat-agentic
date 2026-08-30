export type ProviderId = 'openai' | 'deepseek' | 'anthropic' | 'google' | 'local' | 'openai-compatible'

export type ProviderStatus = 'ready' | 'not-configured' | 'coming-soon'

export interface ModelProvider {
  id: ProviderId
  name: string
  shortName: string
  status: ProviderStatus
  models: string[]
}

export interface ProviderAdapter {
  readonly provider: ModelProvider
  send(input: string, options?: { model?: string }): Promise<AsyncIterable<string>>
}

export const providers: ModelProvider[] = [
  { id: 'openai', name: 'OpenAI / Codex', shortName: 'Codex', status: 'not-configured', models: ['gpt-5.6-terra', 'gpt-5.5'] },
  { id: 'deepseek', name: 'DeepSeek', shortName: 'DeepSeek', status: 'coming-soon', models: ['deepseek-chat'] },
  { id: 'anthropic', name: 'Anthropic', shortName: 'Claude', status: 'coming-soon', models: ['claude-sonnet'] },
  { id: 'google', name: 'Google', shortName: 'Gemini', status: 'coming-soon', models: ['gemini-pro'] },
  { id: 'local', name: 'Local model', shortName: 'Local', status: 'coming-soon', models: ['ollama'] },
  { id: 'openai-compatible', name: 'OpenAI-compatible', shortName: 'Compatible', status: 'coming-soon', models: ['custom'] },
]
