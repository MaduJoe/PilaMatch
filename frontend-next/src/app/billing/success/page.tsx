'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import api from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';

function BillingSuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const authKey = searchParams.get('authKey');
    const customerKey = searchParams.get('customerKey');

    if (!authKey || !customerKey) {
      setStatus('error');
      setMessage('필수 파라미터가 누락되었습니다.');
      return;
    }

    api.subscriptions
      .registerBillingKey({ auth_key: authKey, customer_key: customerKey })
      .then((res) => {
        setStatus('success');
        setMessage(res.message);
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.message || '빌링키 등록에 실패했습니다.');
      });
  }, [searchParams]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 pt-6 text-center">
          {status === 'processing' && (
            <>
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <p className="text-lg font-medium">결제 수단 등록 중...</p>
              <p className="text-sm text-muted-foreground">잠시만 기다려주세요.</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle2 className="h-12 w-12 text-green-500" />
              <p className="text-lg font-medium">등록 완료!</p>
              <p className="text-sm text-muted-foreground">{message}</p>
              <Button
                className="min-h-[44px] w-full"
                onClick={() => router.push('/steps/profile')}
              >
                프로필로 돌아가기
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="h-12 w-12 text-red-500" />
              <p className="text-lg font-medium">등록 실패</p>
              <p className="text-sm text-muted-foreground">{message}</p>
              <Button
                className="min-h-[44px] w-full"
                onClick={() => router.push('/steps/profile')}
              >
                프로필로 돌아가기
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  );
}
