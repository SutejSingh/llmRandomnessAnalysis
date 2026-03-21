/**
 * API may return null for statistics that were NaN/Inf on the server (JSON cannot encode those).
 * Never call .toFixed on raw values — use this helper.
 */
export function formatFixed(value: unknown, digits: number, naLabel: string): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return naLabel
  return value.toFixed(digits)
}
