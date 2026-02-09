import en from './locales/en.json'

type Messages = typeof en

function get(obj: unknown, path: string): string | undefined {
  const keys = path.split('.')
  let current: unknown = obj
  for (const key of keys) {
    if (current == null || typeof current !== 'object') return undefined
    current = (current as Record<string, unknown>)[key]
  }
  return typeof current === 'string' ? current : undefined
}

function interpolate(text: string, vars: Record<string, string | number>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    return key in vars ? String(vars[key]) : `{{${key}}}`
  })
}

/**
 * Get a translated string by dot path. Supports interpolation: use {{varName}} in en.json and pass { varName: value }.
 */
export function t(key: string, vars?: Record<string, string | number>): string {
  const value = get(en, key)
  const text = value ?? key
  return vars ? interpolate(text, vars) : text
}

export type { Messages }
