'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api-client';
import { APIError } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Loader2, XCircle } from 'lucide-react';
import Link from 'next/link';

function PaymentSuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'confirming' | 'success' | 'error'>('confirming');
  const [errorMessage, setErrorMessage] = useState('');

  const paymentKey = searchParams.get('paymentKey');
  const orderId = searchParams.get('orderId');
  const amount = searchParams.get('amount');

  const confirmPayment = useMutation<unknown, Error>({
    mutationFn: () => {
      if (!paymentKey || !orderId || !amount) {
        throw new Error('결제 정보가 누락되었습니다');
      }

      return api.subscriptions.confirmPayment({
        payment_key: paymentKey,
        order_id: orderId,
      });
    },
    onSuccess: () => {
      setStatus('success');
    },
    onError: (error: Error) => {
      setStatus('error');
      setErrorMessage(error instanceof APIError ? error.message : error.message);
    },
  });

  useEffect(() => {
    if (paymentKey && orderId && amount) {
      confirmPayment.mutate();
    } else {
      setStatus('error');
      setErrorMessage('결제 정보가 누락되었습니다');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center justify-center gap-2">
            {status === 'confirming' && (
              <>
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <span>결제 확인 중...</span>
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircle2 className="h-6 w-6 text-green-500" />
                <span className="text-green-600">결제 완료</span>
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="h-6 w-6 text-red-500" />
                <span className="text-red-600">결제 실패</span>
              </>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-center">
          {status === 'confirming' && (
            <p className="text-sm text-gray-500">결제를 확인하고 있습니다. 잠시만 기다려주세요.</p>
          )}
          {status === 'success' && (
            <>
              <p className="text-sm text-gray-500">결제가 성공적으로 완료되었습니다!</p>
              {orderId && <p className="text-xs text-gray-400">주문번호: {orderId}</p>}
              <Button asChild className="w-full">
                <Link href="/settings">설정으로 돌아가기</Link>
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <p className="text-sm text-gray-500">{errorMessage}</p>
              <Button asChild className="w-full">
                <Link href="/settings">돌아가기</Link>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      }
    >
      <PaymentSuccessContent />
    </Suspense>
  );
}
