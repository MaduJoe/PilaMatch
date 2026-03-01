/**
 * Token management abstraction for hybrid web/app mode.
 *
 * - Web: Uses httpOnly cookies via BFF (existing behavior, no token handling needed)
 * - App (Capacitor): Uses SecureStorage for token persistence
 */

import { Capacitor } from '@capacitor/core';

// Dynamic import to avoid bundling Capacitor plugins in web builds
let SecureStoragePlugin: any = null;

async function getSecureStorage() {
  if (!SecureStoragePlugin) {
    try {
      const mod = await import('@nicepay/capacitor-secure-storage');
      SecureStoragePlugin = mod.SecureStorage;
    } catch {
      // Fallback: use localStorage (less secure, for dev/testing only)
      SecureStoragePlugin = {
        async set({ key, value }: { key: string; value: string }) {
          localStorage.setItem(key, value);
        },
        async get({ key }: { key: string }) {
          return { value: localStorage.getItem(key) };
        },
        async remove({ key }: { key: string }) {
          localStorage.removeItem(key);
        },
      };
    }
  }
  return SecureStoragePlugin;
}

export function isNativePlatform(): boolean {
  try {
    return Capacitor.isNativePlatform();
  } catch {
    return false;
  }
}

export async function getAccessToken(): Promise<string | null> {
  if (!isNativePlatform()) return null; // Web uses cookies

  const storage = await getSecureStorage();
  try {
    const result = await storage.get({ key: 'access_token' });
    return result.value || null;
  } catch {
    return null;
  }
}

export async function getRefreshToken(): Promise<string | null> {
  if (!isNativePlatform()) return null;

  const storage = await getSecureStorage();
  try {
    const result = await storage.get({ key: 'refresh_token' });
    return result.value || null;
  } catch {
    return null;
  }
}

export async function setTokens(accessToken: string, refreshToken: string): Promise<void> {
  if (!isNativePlatform()) return;

  const storage = await getSecureStorage();
  await storage.set({ key: 'access_token', value: accessToken });
  await storage.set({ key: 'refresh_token', value: refreshToken });
}

export async function clearTokens(): Promise<void> {
  if (!isNativePlatform()) return;

  const storage = await getSecureStorage();
  await storage.remove({ key: 'access_token' });
  await storage.remove({ key: 'refresh_token' });
}
