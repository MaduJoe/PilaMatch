'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';
import Link from 'next/link';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Unhandled error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
        <AlertTriangle className="h-8 w-8 text-destructive" />
      </div>
      <h2 className="mb-2 text-2xl font-bold">문제가 발생했습니다</h2>
      <p className="mb-6 max-w-md text-muted-foreground">
        일시적인 오류가 발생했습니다. 다시 시도하거나, 문제가 계속되면 홈으로
        돌아가주세요.
      </p>
      <div className="flex gap-3">
        <Button onClick={reset} variant="outline">
          <RotateCcw className="mr-2 h-4 w-4" />
          다시 시도
        </Button>
        <Button asChild>
          <Link href="/">
            <Home className="mr-2 h-4 w-4" />
            홈으로
          </Link>
        </Button>
      </div>
    </div>
  );
}
