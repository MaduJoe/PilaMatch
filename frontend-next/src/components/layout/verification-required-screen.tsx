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
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-6 animate-fade-up">
      <div className="flex flex-col items-center gap-5 text-center max-w-sm">
        <div className="flex size-20 items-center justify-center rounded-2xl bg-primary/10">
          <Shield
            className="size-10 text-primary"
            strokeWidth={1.5}
            aria-hidden="true"
          />
        </div>
        <div className="space-y-2">
          <h1 className="font-display text-xl font-bold tracking-tight">
            {isInstructor ? '본인 인증 필요' : '인증 필요'}
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {isInstructor
              ? '휴대폰 인증을 완료하면 공고에 지원할 수 있습니다.'
              : '휴대폰 인증과 사업자 인증을 모두 완료해야 공고를 등록할 수 있습니다.'}
          </p>
        </div>
        <Button asChild className="mt-2 min-h-[48px] px-8 font-display font-semibold">
          <Link href="/steps/profile">인증하러 가기</Link>
        </Button>
      </div>
    </div>
  );
}
