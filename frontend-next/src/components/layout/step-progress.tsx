'use client';

import { cn } from '@/lib/utils';
import { Check, Lock } from 'lucide-react';

interface StepProgressProps {
  steps: readonly { key: string; label: string; path: string }[];
  currentStep: number; // 0-indexed
}

export function StepProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <div className="mx-auto max-w-4xl px-4 py-3">
      <div className="flex gap-2">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;
          const isFuture = index > currentStep;

          return (
            <div
              key={step.key}
              className={cn(
                'flex flex-1 flex-col items-center rounded-lg border-2 px-2 py-2 text-center transition-colors',
                isCompleted && 'border-green-500 bg-green-50',
                isCurrent && 'border-yellow-500 bg-yellow-50',
                isFuture && 'border-gray-200 bg-gray-50',
              )}
              role="listitem"
              aria-label={`${step.label}: ${isCompleted ? '완료' : isCurrent ? '현재 단계' : '잠김'}`}
            >
              <div className="mb-1">
                {isCompleted ? (
                  <Check className="h-5 w-5 text-green-600" aria-hidden="true" />
                ) : isCurrent ? (
                  <span className="text-lg font-bold text-yellow-700" aria-hidden="true">
                    {index + 1}
                  </span>
                ) : (
                  <Lock className="h-4 w-4 text-gray-400" aria-hidden="true" />
                )}
              </div>
              <span
                className={cn(
                  'truncate text-xs font-medium',
                  isCompleted && 'text-green-800',
                  isCurrent && 'text-yellow-800',
                  isFuture && 'text-gray-500',
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
