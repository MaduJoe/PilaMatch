'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import api from '@/lib/api-client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Crown, Check, Mail, UserCircle } from 'lucide-react';
import { TossCheckoutButton } from '@/components/payment/toss-checkout-button';

// ---------------------------------------------------------------------------
// Premium benefits
// ---------------------------------------------------------------------------

const PRO_BENEFITS = [
  '전 지역 지원/공고 가능',
  '긴급 공고 무제한 접근',
  '일일 지원 횟수 무제한',
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const { user } = useAuthStore();
  const logout = useLogout();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const subQuery = useQuery({
    queryKey: ['my-subscription'],
    queryFn: () => api.subscriptions.getStatus(),
  });

  const cancelSubMutation = useMutation({
    mutationFn: () => api.subscriptions.cancel(),
    onSuccess: () => {
      toast.success('구독이 해지되었습니다.');
      subQuery.refetch();
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail?.message || err?.message || '해지에 실패했습니다.';
      toast.error(msg);
    },
  });

  const isPremium = subQuery.data?.has_subscription === true;
  const isCancelled = subQuery.data?.subscription?.status === 'cancelled';
  const cancelledEndDate = subQuery.data?.subscription?.end_date?.slice(0, 10);

  const handleDelete = async () => {
    if (!password.trim()) {
      setError('비밀번호를 입력해주세요.');
      return;
    }

    setError(null);
    setIsDeleting(true);
    try {
      const res = await fetch('/api/v1/auth/users/me', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const message =
          typeof body.detail === 'string'
            ? body.detail
            : body.detail?.message || '계정 삭제에 실패했습니다.';
        throw new Error(message);
      }

      logout.mutate();
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '계정 삭제에 실패했습니다.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-up">
      <h1 className="font-display text-2xl font-bold tracking-tight">설정</h1>

      {/* Account info */}
      <Card>
        <CardHeader>
          <CardTitle className="font-display">계정 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-muted">
              <Mail className="size-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display">이메일</p>
              <p className="font-medium">{user?.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-muted">
              <UserCircle className="size-4 text-muted-foreground" />
            </div>
            <div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display">역할</p>
              <p className="font-medium">{user?.role === 'instructor' ? '강사' : '스튜디오'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subscription */}
      <Card className={isPremium && !isCancelled ? 'border-amber-300/50 dark:border-amber-700/50' : 'border-primary/20'}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="font-display flex items-center gap-2">
              <Crown className="size-5 text-amber-500" />
              구독
            </CardTitle>
            {isPremium && !isCancelled ? (
              <Badge className="bg-amber-500 text-white hover:bg-amber-600 font-display text-[10px] uppercase tracking-wider">이용 중</Badge>
            ) : isCancelled ? (
              <Badge variant="outline" className="border-amber-300 text-amber-600 font-display text-[10px] uppercase tracking-wider">해지 예정</Badge>
            ) : (
              <Badge variant="outline" className="font-display text-[10px] uppercase tracking-wider">무료</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isPremium && !isCancelled ? (
            /* Active premium */
            <div className="space-y-3">
              <p className="text-sm">
                <span className="font-display text-2xl font-bold">9,900</span>
                <span className="ml-1 text-muted-foreground">원/월</span>
                <span className="ml-2 text-xs text-muted-foreground">
                  다음 결제: {subQuery.data?.subscription?.next_billing_date?.slice(0, 10) ?? '-'}
                </span>
              </p>
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                onClick={() => cancelSubMutation.mutate()}
                disabled={cancelSubMutation.isPending}
              >
                {cancelSubMutation.isPending ? '해지 중...' : '구독 해지'}
              </Button>
            </div>
          ) : isCancelled ? (
            /* Cancelled but still within period */
            <div className="space-y-4">
              <div className="rounded-xl bg-amber-50 dark:bg-amber-950/20 p-4">
                <p className="text-sm text-amber-700 dark:text-amber-400">
                  {cancelledEndDate}까지 프리미엄 혜택을 이용할 수 있습니다.
                </p>
              </div>
              <TossCheckoutButton userName={user?.display_name ?? undefined} userEmail={user?.email ?? undefined} />
            </div>
          ) : (
            /* Free */
            <div className="space-y-4">
              <div className="rounded-xl bg-muted/40 p-4 space-y-2.5">
                {PRO_BENEFITS.map((b) => (
                  <div key={b} className="flex items-start gap-2.5 text-sm">
                    <div className="mt-0.5 flex size-5 items-center justify-center rounded-md bg-primary/10">
                      <Check className="size-3 text-primary" />
                    </div>
                    <span>{b}</span>
                  </div>
                ))}
              </div>
              <div className="text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-display mb-1">월 정기결제</p>
                <p className="font-display text-3xl font-bold">9,900<span className="text-base font-normal text-muted-foreground ml-0.5">원</span></p>
              </div>
              <TossCheckoutButton userName={user?.display_name ?? undefined} userEmail={user?.email ?? undefined} />
            </div>
          )}
        </CardContent>
      </Card>

      <Button
        variant="outline"
        className="w-full min-h-[44px] font-display"
        onClick={() => logout.mutate()}
      >
        로그아웃
      </Button>

      {/* Account deletion */}
      <Card>
        <CardHeader>
          <CardTitle className="font-display">계정 삭제</CardTitle>
          <CardDescription>
            모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="font-display min-h-[44px] text-muted-foreground">계정 삭제</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-display">삭제 확인</DialogTitle>
                <DialogDescription asChild>
                  <div className="space-y-2">
                    <p>진행 전 아래 내용을 확인해주세요:</p>
                    <ul className="list-inside list-disc space-y-1 text-sm">
                      <li>30일 이내 복구 가능</li>
                      <li>진행 중인 계약이 취소됩니다</li>
                      <li>공고 및 지원 내역이 삭제됩니다</li>
                    </ul>
                  </div>
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="delete-password">비밀번호</Label>
                  <Input
                    id="delete-password"
                    type="password"
                    placeholder="비밀번호 입력"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                {error && (
                  <p className="text-sm text-red-500">{error}</p>
                )}
              </div>

              <DialogFooter className="gap-2 sm:gap-0">
                <Button
                  variant="outline"
                  onClick={() => {
                    setOpen(false);
                    setPassword('');
                    setError(null);
                  }}
                >
                  취소
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={isDeleting || !password.trim()}
                >
                  {isDeleting ? '삭제 중...' : '삭제'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
