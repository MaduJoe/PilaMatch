/* eslint-disable no-undef */

/**
 * Firebase Messaging Service Worker.
 * Handles background push notifications when the app is not in the foreground.
 *
 * Firebase config is injected by the main app via __FIREBASE_CONFIG__ global,
 * or falls back to empty strings (no-op if not configured).
 */
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: self.__FIREBASE_CONFIG__?.apiKey || '',
  authDomain: self.__FIREBASE_CONFIG__?.authDomain || '',
  projectId: self.__FIREBASE_CONFIG__?.projectId || '',
  storageBucket: self.__FIREBASE_CONFIG__?.storageBucket || '',
  messagingSenderId: self.__FIREBASE_CONFIG__?.messagingSenderId || '',
  appId: self.__FIREBASE_CONFIG__?.appId || '',
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification || {};
  if (!title) return;

  self.registration.showNotification(title, {
    body: body || '',
    icon: '/icon-192.svg',
    badge: '/icon-192.svg',
    data: payload.data,
    tag: payload.data?.type || 'default',
    // Keep urgent substitute notifications visible until dismissed
    requireInteraction: payload.data?.type === 'urgent_substitute',
  });
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const data = event.notification.data;
  let url = '/';

  if (data?.type === 'urgent_substitute' && data?.job_id) {
    url = `/steps/jobs?highlight=${data.job_id}`;
  } else if (data?.type === 'application_accepted' && data?.job_id) {
    url = `/steps/applications`;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Focus existing window if available
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(url);
          return client.focus();
        }
      }
      // Otherwise open a new window
      return clients.openWindow(url);
    }),
  );
});
