/**
 * Token management for web mode.
 *
 * Web uses httpOnly cookies via BFF — no client-side token handling needed.
 * Capacitor/native support removed for PMF phase (web-only).
 */

export function isNativePlatform(): boolean {
  return false;
}

export async function getAccessToken(): Promise<string | null> {
  return null; // Web uses cookies
}

export async function getRefreshToken(): Promise<string | null> {
  return null;
}

export async function setTokens(_accessToken: string, _refreshToken: string): Promise<void> {
  // no-op for web
}

export async function clearTokens(): Promise<void> {
  // no-op for web
}
