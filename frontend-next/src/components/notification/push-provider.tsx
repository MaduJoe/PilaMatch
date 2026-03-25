'use client';

import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores/auth-store';
import {
  requestNotificationPermission,
  onForegroundMessage,
} from '@/lib/firebase';
import { notifications } from '@/lib/api-client';

/**
 * PushNotificationProvider
 *
 * - Requests notification permission after the user authenticates
 * - Registers the FCM device token with the backend
 * - Shows foreground push messages as toast notifications
 *
 * Wrap this around (or alongside) the authenticated page tree.
 * Gracefully no-ops when Firebase is not configured or notifications are unsupported.
 */
export function PushNotificationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated } = useAuthStore();
  const registered = useRef(false);

  // Register device token once after authentication
  useEffect(() => {
    if (!isAuthenticated || !user || registered.current) return;
    if (typeof window === 'undefined' || !('Notification' in window)) return;

    let cancelled = false;

    async function setup() {
      const token = await requestNotificationPermission();
      if (!token || cancelled) return;

      try {
        await notifications.registerDeviceToken(token, 'web');
        registered.current = true;
      } catch (err) {
        console.error('[FCM] Failed to register device token:', err);
      }
    }

    setup();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, user]);

  // Listen for foreground messages
  useEffect(() => {
    const unsubscribe = onForegroundMessage((payload) => {
      const { title, body } = payload.notification || {};
      if (!title) return;

      const notificationType = payload.data?.type;

      // --- Dispatch-specific notification types ---
      if (notificationType === 'dispatch_incoming') {
        toast(title, {
          description: body,
          duration: 10000,
          action: {
            label: '확인',
            onClick: () => {
              window.location.href = '/dashboard';
            },
          },
        });
        return;
      }

      if (notificationType === 'dispatch_accepted') {
        toast.success(title, {
          description: body,
          duration: 8000,
          action: {
            label: '연락처 보기',
            onClick: () => {
              window.location.href = '/steps/offers';
            },
          },
        });
        return;
      }

      if (notificationType === 'checkin_completed') {
        toast.success(body || title, {
          duration: 5000,
        });
        return;
      }

      // --- Existing notification types ---
      const isUrgent = notificationType === 'urgent_substitute';

      toast(title, {
        description: body,
        duration: isUrgent ? 8000 : 4000,
        action: payload.data?.job_id
          ? {
              label: '보기',
              onClick: () => {
                window.location.href = `/steps/jobs?highlight=${payload.data!.job_id}`;
              },
            }
          : undefined,
      });
    });

    return () => {
      unsubscribe?.();
    };
  }, []);

  return <>{children}</>;
}
