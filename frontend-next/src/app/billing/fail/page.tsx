'use client';

import { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, XCircle } from 'lucide-react';

function BillingFailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const code = searchParams.get('code') || 'UNKNOWN';
  const message = searchParams.get('message') || '결제 수단 등록에 실패했습니다.';

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 pt-6 text-center">
          <XCircle className="h-12 w-12 text-red-500" />
          <p className="text-lg font-medium">결제 등록 실패</p>
          <p className="text-sm text-muted-foreground">{message}</p>
          <p className="text-xs text-muted-foreground">오류 코드: {code}</p>
          <Button
            className="min-h-[44px] w-full"
            onClick={() => router.push('/steps/profile')}
          >
            프로필로 돌아가기
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

export default function BillingFailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <BillingFailContent />
    </Suspense>
  );
}
