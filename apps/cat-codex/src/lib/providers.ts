export type ProviderId = 'openai' | 'anthropic' | 'google' | 'deepseek' | 'grok' | 'mistral' | 'zhipu' | 'kimi' | 'minimax' | 'qwen' | 'qianfan' | 'openrouter' | 'groq' | 'together' | 'fireworks' | 'ollama' | 'lm-studio' | 'azure-openai' | 'bedrock' | 'github-models' | 'local' | 'openai-compatible'

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
  { id: 'openai', name: 'OpenAI / Codex', shortName: 'Codex', status: 'not-configured', models: ['gpt-5.6-terra', 'gpt-5.6-sol', 'gpt-5.6-luna'] },
  { id: 'anthropic', name: 'Anthropic', shortName: 'Claude', status: 'coming-soon', models: ['claude-sonnet-4-6', 'claude-opus-4-6', 'claude-haiku-4-5-20251001'] },
  { id: 'google', name: 'Google', shortName: 'Gemini', status: 'coming-soon', models: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite'] },
  { id: 'deepseek', name: 'DeepSeek', shortName: 'DeepSeek', status: 'coming-soon', models: ['deepseek-v4-pro', 'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp'] },
  { id: 'grok', name: 'xAI', shortName: 'Grok', status: 'coming-soon', models: ['grok-4.6'] },
  { id: 'mistral', name: 'Mistral AI', shortName: 'Mistral', status: 'coming-soon', models: ['mistral-large-latest', 'mistral-small-latest'] },
  { id: 'zhipu', name: 'Zhipu AI', shortName: 'GLM', status: 'coming-soon', models: ['glm-4.5', 'glm-4.5-air'] },
  { id: 'kimi', name: 'Moonshot AI', shortName: 'Kimi', status: 'coming-soon', models: ['kimi-k2.6'] },
  { id: 'minimax', name: 'MiniMax', shortName: 'MiniMax', status: 'coming-soon', models: ['MiniMax-M2.7', 'MiniMax-M2.5', 'MiniMax-M2.1'] },
  { id: 'qwen', name: 'Alibaba Qwen', shortName: '通义千问', status: 'coming-soon', models: ['qwen3.7-max', 'qwen3.7-plus'] },
  { id: 'qianfan', name: 'Baidu Qianfan', shortName: '千帆', status: 'coming-soon', models: ['ernie-4.5-turbo'] },
  { id: 'openrouter', name: 'OpenRouter', shortName: 'OpenRouter', status: 'coming-soon', models: ['openai/gpt-4o', 'google/gemini-2.5-pro'] },
  { id: 'groq', name: 'Groq', shortName: 'Groq', status: 'coming-soon', models: ['meta-llama/llama-4-scout-17b-16e-instruct', 'openai/gpt-oss-120b'] },
  { id: 'together', name: 'Together AI', shortName: 'Together', status: 'coming-soon', models: ['meta-llama/Llama-4-Scout'] },
  { id: 'fireworks', name: 'Fireworks AI', shortName: 'Fireworks', status: 'coming-soon', models: ['accounts/fireworks/models/llama-v4-scout-instruct-basic'] },
  { id: 'ollama', name: 'Ollama', shortName: 'Ollama', status: 'coming-soon', models: ['llama3.3'] },
  { id: 'lm-studio', name: 'LM Studio', shortName: 'LM Studio', status: 'coming-soon', models: ['local-model'] },
  { id: 'azure-openai', name: 'Azure OpenAI', shortName: 'Azure', status: 'coming-soon', models: ['gpt-4o'] },
  { id: 'bedrock', name: 'AWS Bedrock', shortName: 'Bedrock', status: 'coming-soon', models: ['anthropic.claude-sonnet-4-6'] },
  { id: 'github-models', name: 'GitHub Models', shortName: 'GitHub', status: 'coming-soon', models: ['openai/gpt-4.1'] },
  { id: 'local', name: 'Local model', shortName: 'Local', status: 'coming-soon', models: ['llama3.3'] },
  { id: 'openai-compatible', name: '自定义服务商', shortName: '自定义', status: 'not-configured', models: ['自定义模型 ID'] },
]
