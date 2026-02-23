'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface StepNavigationProps {
  steps: readonly { key: string; label: string; path: string }[];
  currentStep: number; // 0-indexed
}

export function StepNavigation({ steps, currentStep }: StepNavigationProps) {
  const pathname = usePathname();

  return (
    <nav className="mx-auto max-w-4xl px-4" aria-label="단계 네비게이션">
      <div className="flex gap-2">
        {steps.map((step, index) => {
          const isCurrentPage = pathname === step.path;
          const isAccessible = index <= currentStep;

          if (isCurrentPage) {
            return (
              <Button
                key={step.key}
                className="flex-1"
                variant="default"
                size="sm"
                disabled
                aria-current="page"
              >
                {step.label}
              </Button>
            );
          }

          if (isAccessible) {
            return (
              <Button
                key={step.key}
                className="flex-1"
                variant="outline"
                size="sm"
                asChild
              >
                <Link href={step.path}>{step.label}</Link>
              </Button>
            );
          }

          return (
            <Button
              key={step.key}
              className="flex-1"
              variant="ghost"
              size="sm"
              disabled
              aria-disabled="true"
            >
              {step.label}
            </Button>
          );
        })}
      </div>
    </nav>
  );
}
