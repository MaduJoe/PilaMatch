'use client';

import Link from 'next/link';
import { Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface VerificationRequiredScreenProps {
  role: 'instructor' | 'studio';
}

export function VerificationRequiredScreen({ role }: VerificationRequiredScreenProps) {
  const isInstructor = role === 'instructor';

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <Shield
          className="size-16 text-primary/40"
          aria-hidden="true"
        />
        <h1 className="text-xl font-semibold">
          {isInstructor ? '본인인증이 필요합니다' : '사업자 인증이 필요합니다'}
        </h1>
        <p className="text-sm text-muted-foreground">
          {isInstructor
            ? '서비스 이용을 위해 본인인증을 완료해주세요.'
            : '서비스 이용을 위해 사업자 인증을 완료해주세요.'}
        </p>
        <Button asChild className="mt-2 min-h-[48px]">
          <Link href="/steps/profile">인증하러 가기</Link>
        </Button>
      </div>
    </div>
  );
}
