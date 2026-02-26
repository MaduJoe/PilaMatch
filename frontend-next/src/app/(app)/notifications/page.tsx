'use client';

import { useEffect, useState, useCallback } from 'react';
import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { formatDateTime } from '@/lib/utils';

interface Notification {
  id: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  link?: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchNotifications = useCallback(async (pageNum: number) => {
    try {
      const res = await fetch(
        `/api/v1/notifications?page=${pageNum}&limit=20`,
        { credentials: 'include' },
      );
      if (res.ok) {
        const data = await res.json();
        const items: Notification[] = data.items ?? data ?? [];
        if (pageNum === 1) {
          setNotifications(items);
        } else {
          setNotifications((prev) => [...prev, ...items]);
        }
        setHasMore(items.length === 20);
      }
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications(1);
  }, [fetchNotifications]);

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    fetchNotifications(next);
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">알림</h1>

      {notifications.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Bell className="mb-3 h-12 w-12 text-muted-foreground" />
            <p className="text-muted-foreground">새로운 알림이 없습니다</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-2">
            {notifications.map((n) => (
              <Card
                key={n.id}
                className={!n.is_read ? 'border-primary/30 bg-accent/30' : ''}
              >
                <CardContent className="flex items-start gap-3 py-4">
                  <div
                    className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                      n.is_read ? 'bg-transparent' : 'bg-primary'
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium">{n.title}</p>
                    <p className="text-sm text-muted-foreground">{n.body}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDateTime(n.created_at)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {hasMore && (
            <div className="text-center">
              <Button variant="outline" onClick={loadMore}>
                더 보기
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
