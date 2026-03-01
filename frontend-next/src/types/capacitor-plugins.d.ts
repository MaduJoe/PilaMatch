/**
 * Type declarations for Capacitor plugins that are only available at runtime
 * on native platforms. These are dynamically imported with a localStorage fallback.
 */

declare module '@nicepay/capacitor-secure-storage' {
  export const SecureStorage: {
    set(options: { key: string; value: string }): Promise<void>;
    get(options: { key: string }): Promise<{ value: string | null }>;
    remove(options: { key: string }): Promise<void>;
  };
}
