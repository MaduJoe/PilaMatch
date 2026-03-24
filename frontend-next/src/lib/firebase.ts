/**
 * Firebase Cloud Messaging (FCM) setup for push notifications.
 *
 * All functions gracefully return null when:
 *  - Running on the server (SSR)
 *  - Browser does not support Notification API
 *  - Firebase env vars are not configured
 */
import { initializeApp, getApps } from 'firebase/app';
import {
  getMessaging,
  getToken,
  onMessage,
  type Messaging,
} from 'firebase/messaging';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

/** True when all required Firebase config values are present. */
function isFirebaseConfigured(): boolean {
  return !!(firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.messagingSenderId);
}

// Initialize Firebase app (singleton)
const app =
  isFirebaseConfigured()
    ? getApps().length === 0
      ? initializeApp(firebaseConfig)
      : getApps()[0]
    : null;

let messaging: Messaging | null = null;

function getMessagingInstance(): Messaging | null {
  if (typeof window === 'undefined') return null;
  if (!app) return null;
  if (!messaging) {
    try {
      messaging = getMessaging(app);
    } catch {
      console.warn('[FCM] Messaging not supported in this browser');
    }
  }
  return messaging;
}

/**
 * Request notification permission and return the FCM token.
 * Returns null if permission is denied or FCM is unavailable.
 */
export async function requestNotificationPermission(): Promise<string | null> {
  if (typeof window === 'undefined' || !('Notification' in window)) return null;
  if (!isFirebaseConfigured()) return null;

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') return null;

    const msg = getMessagingInstance();
    if (!msg) return null;

    const token = await getToken(msg, {
      vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
    });
    return token;
  } catch (error) {
    console.error('[FCM] Failed to get token:', error);
    return null;
  }
}

/**
 * Listen for foreground push messages.
 * Returns an unsubscribe function, or null if messaging is unavailable.
 */
export function onForegroundMessage(
  callback: (payload: { notification?: { title?: string; body?: string }; data?: Record<string, string> }) => void,
): (() => void) | null {
  const msg = getMessagingInstance();
  if (!msg) return null;
  return onMessage(msg, callback);
}
