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
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, Crown, Check, Loader2, Mail, UserCircle } from 'lucide-react';
import { TierCard } from '@/components/trust/tier-card';

// ---------------------------------------------------------------------------
// Premium benefits
// ---------------------------------------------------------------------------

const PRO_BENEFITS = [
  '전 지역 지원/공고 가능',
  '긴급 공고 무제한 접근',
  '일일 지원 횟수 무제한',
];

// ---------------------------------------------------------------------------
// Upgrade button with depositor name dialog
// ---------------------------------------------------------------------------

function UpgradeButton({ onUpgrade, isPending }: { onUpgrade: (name: string) => void; isPending: boolean }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [depositorName, setDepositorName] = useState('');

  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      <DialogTrigger asChild>
        <Button className="min-h-[48px] w-full text-base font-display font-semibold">
          프리미엄 구독하기
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-display">프리미엄 구독</DialogTitle>
          <DialogDescription>
            입금자명을 입력하시면 계좌이체 안내를 받으실 수 있습니다.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="depositor-name">입금자명</Label>
            <Input
              id="depositor-name"
              placeholder="홍길동"
              className="min-h-[44px]"
              value={depositorName}
              onChange={(e) => setDepositorName(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setDialogOpen(false)}>
            취소
          </Button>
          <Button
            disabled={isPending || !depositorName.trim()}
            onClick={() => {
              onUpgrade(depositorName.trim());
              setDialogOpen(false);
            }}
          >
            {isPending ? <Loader2 className="mr-1 size-4 animate-spin" /> : null}
            {isPending ? '처리 중...' : '이체 요청'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

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

  const tierQuery = useQuery({
    queryKey: ['my-tier'],
    queryFn: () => api.tier.getMyTier(),
  });
  const subQuery = useQuery({
    queryKey: ['my-subscription'],
    queryFn: () => api.subscriptions.getStatus(),
  });

  const bankTransferMutation = useMutation({
    mutationFn: (name: string) => api.subscriptions.initBankTransfer({ depositor_name: name }),
    onSuccess: () => {
      toast.success('이체 요청이 접수되었습니다. 확인 후 자동 활성화됩니다.');
    },
    onError: () => toast.error('요청에 실패했습니다. 다시 시도해주세요.'),
  });

  const cancelSubMutation = useMutation({
    mutationFn: () => api.subscriptions.cancel(),
    onSuccess: () => {
      toast.success('구독이 해지되었습니다.');
      subQuery.refetch();
      tierQuery.refetch();
    },
    onError: () => toast.error('해지에 실패했습니다.'),
  });

  const isPremium = subQuery.data?.has_subscription === true;

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

      {/* Tier card */}
      {tierQuery.data && <TierCard data={tierQuery.data} />}

      {/* Subscription */}
      <Card className={isPremium ? 'border-amber-300/50 dark:border-amber-700/50' : 'border-primary/20'}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="font-display flex items-center gap-2">
              <Crown className="size-5 text-amber-500" />
              구독
            </CardTitle>
            {isPremium ? (
              <Badge className="bg-amber-500 text-white hover:bg-amber-600 font-display text-[10px] uppercase tracking-wider">이용 중</Badge>
            ) : (
              <Badge variant="outline" className="font-display text-[10px] uppercase tracking-wider">무료</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isPremium ? (
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
          ) : (
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
              <UpgradeButton
                onUpgrade={(name) => bankTransferMutation.mutate(name)}
                isPending={bankTransferMutation.isPending}
              />
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

      {/* Danger zone */}
      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="font-display text-destructive">계정 삭제</CardTitle>
          <CardDescription>
            모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" className="font-display">계정 삭제</Button>
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
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    비밀번호를 입력하여 확인해주세요.
                  </AlertDescription>
                </Alert>

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
                  <p className="text-sm text-destructive">{error}</p>
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
