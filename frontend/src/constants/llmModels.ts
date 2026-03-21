/** Provider id values sent to the API (must match backend). */
export type ProviderId = 'openai' | 'anthropic' | 'deepseek'

export interface ModelOption {
  /** Exact model id for the provider API (e.g. gpt-5.4, claude-sonnet-4-6) */
  value: string
  label: string
}

/** Default model when switching provider or on first load */
export const DEFAULT_MODEL_BY_PROVIDER: Record<ProviderId, string> = {
  openai: 'gpt-5.4',
  anthropic: 'claude-sonnet-4-6',
  deepseek: 'deepseek-chat',
}

export const MODEL_OPTIONS: Record<ProviderId, ModelOption[]> = {
  openai: [
    { value: 'gpt-5.4', label: 'GPT-5.4' },
    { value: 'gpt-5.4-nano', label: 'GPT-5.4 nano' },
    { value: 'gpt-5.4-mini', label: 'GPT-5.4 mini' },
    { value: 'gpt-5.4-pro', label: 'GPT-5.4 pro' },
    { value: 'gpt-5-mini', label: 'GPT-5 mini' },
    { value: 'gpt-5-nano', label: 'GPT-5 nano' },
    { value: 'gpt-5', label: 'GPT-5' },
    { value: 'gpt-4.1', label: 'GPT-4.1' },
  ],
  anthropic: [
    { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
    { value: 'claude-haiku-4-5', label: 'Claude Haiku 4.5' },
    { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (snapshot)' },
    { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5' },
    { value: 'claude-opus-4-5', label: 'Claude Opus 4.5' },
    { value: 'claude-opus-4-1', label: 'Claude Opus 4.1' },
    { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4' },
    { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (legacy)' },
  ],
  deepseek: [
    { value: 'deepseek-chat', label: 'DeepSeek Chat (V3.2)' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner (V3.2)' },
  ],
}

export function getDefaultModelForProvider(provider: string): string {
  const p = provider as ProviderId
  if (p in DEFAULT_MODEL_BY_PROVIDER) {
    return DEFAULT_MODEL_BY_PROVIDER[p]
  }
  return DEFAULT_MODEL_BY_PROVIDER.openai
}

export function getModelOptionsForProvider(provider: string): ModelOption[] {
  const p = provider as ProviderId
  if (p in MODEL_OPTIONS) {
    return MODEL_OPTIONS[p]
  }
  return MODEL_OPTIONS.openai
}
