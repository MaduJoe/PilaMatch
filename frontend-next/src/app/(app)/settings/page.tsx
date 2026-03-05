'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
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
import { AlertTriangle } from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const logout = useLogout();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

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

      <Button
        variant="outline"
        className="w-full"
        onClick={() => logout.mutate()}
      >
        로그아웃
      </Button>

      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive">위험 구역</CardTitle>
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
