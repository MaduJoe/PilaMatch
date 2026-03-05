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
import { AlertTriangle, Crown, Check, Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Premium (Pro) benefits — shared for instructor & studio
// ---------------------------------------------------------------------------

const PRO_BENEFITS = [
  '모든 지역 지원/공고 등록 가능 (Basic: 내 위치+1개, Verified: +2개)',
  '긴급건 무제한 지원/등록 (Basic: 1건, Verified: 2건)',
  '일일 지원 무제한',
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
        <Button className="min-h-[48px] w-full text-base font-semibold">
          프리미엄 구독하기
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>프리미엄 구독 — 무통장 입금</DialogTitle>
          <DialogDescription>
            입금자명을 입력하면 계좌 정보를 안내해드립니다. 입금 확인 후 자동 활성화됩니다.
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
            {isPending ? '처리 중...' : '입금 신청'}
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

  // Tier & subscription queries
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
      toast.success('무통장 입금 신청 완료! 입금 확인 후 자동 활성화됩니다.');
    },
    onError: () => toast.error('신청 중 오류가 발생했습니다.'),
  });

  const cancelSubMutation = useMutation({
    mutationFn: () => api.subscriptions.cancel(),
    onSuccess: () => {
      toast.success('구독이 해지되었습니다.');
      subQuery.refetch();
      tierQuery.refetch();
    },
    onError: () => toast.error('해지 중 오류가 발생했습니다.'),
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
            : body.detail?.message || '탈퇴 처리에 실패했습니다.';
        throw new Error(message);
      }

      logout.mutate();
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : '탈퇴 처리에 실패했습니다.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">설정</h1>

      <Card>
        <CardHeader>
          <CardTitle>계정 정보</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">이메일: </span>
            {user?.email}
          </p>
          <p>
            <span className="text-muted-foreground">역할: </span>
            {user?.role === 'instructor' ? '강사' : '스튜디오'}
          </p>
        </CardContent>
      </Card>

      {/* Subscription / Premium section */}
      <Card className={isPremium ? 'border-amber-300 dark:border-amber-700' : 'border-primary/30'}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Crown className="size-5 text-amber-500" />
              Premium Subscription
            </CardTitle>
            {isPremium ? (
              <Badge className="bg-amber-500 text-white hover:bg-amber-600">구독 중</Badge>
            ) : (
              <Badge variant="outline">미구독</Badge>
            )}
          </div>
          {tierQuery.data && (
            <p className="text-sm text-muted-foreground">
              현재 등급: <span className="font-medium">{tierQuery.data.tier_label_ko}({tierQuery.data.tier_label})</span>
            </p>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {isPremium ? (
            /* Already subscribed — show status & cancel */
            <div className="space-y-3">
              <p className="text-sm">
                월 <span className="text-lg font-bold">9,900원</span>
                <span className="ml-1 text-muted-foreground">/ 다음 결제일: {subQuery.data?.subscription?.next_billing_date?.slice(0, 10) ?? '-'}</span>
              </p>
              <Button
                variant="outline"
                size="sm"
                className="min-h-[44px]"
                onClick={() => cancelSubMutation.mutate()}
                disabled={cancelSubMutation.isPending}
              >
                {cancelSubMutation.isPending ? '해지 처리 중...' : '구독 해지'}
              </Button>
            </div>
          ) : (
            /* Not subscribed — show benefits & CTA */
            <div className="space-y-4">
              <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                {PRO_BENEFITS.map((b) => (
                  <div key={b} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span>{b}</span>
                  </div>
                ))}
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground mb-1">월 구독료</p>
                <p className="text-2xl font-bold">9,900<span className="text-base font-normal text-muted-foreground">원</span></p>
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
        className="w-full"
        onClick={() => logout.mutate()}
      >
        로그아웃
      </Button>

      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">계정 삭제</CardTitle>
          <CardDescription>
            회원 탈퇴 시 모든 데이터가 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive">회원 탈퇴</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>정말 탈퇴하시겠습니까?</DialogTitle>
                <DialogDescription asChild>
                  <div className="space-y-2">
                    <p>탈퇴 전 다음 사항을 확인해주세요:</p>
                    <ul className="list-inside list-disc space-y-1 text-sm">
                      <li>30일 내 로그인하면 복구 가능합니다</li>
                      <li>활성 계약은 자동 취소됩니다</li>
                      <li>작성한 공고 및 지원 내역은 삭제됩니다</li>
                    </ul>
                  </div>
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3">
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    본인 확인을 위해 비밀번호를 입력해주세요.
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
                  {isDeleting ? '처리 중...' : '탈퇴'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
