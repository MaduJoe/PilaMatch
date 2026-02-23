'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// ---------------------------------------------------------------------------
// Size map
// ---------------------------------------------------------------------------

const sizeClasses: Record<string, string> = {
  sm: 'size-4',
  md: 'size-5',
  lg: 'size-7',
};

const gapClasses: Record<string, string> = {
  sm: 'gap-0.5',
  md: 'gap-1',
  lg: 'gap-1.5',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function StarRating({
  value,
  onChange,
  readonly = false,
  size = 'md',
}: StarRatingProps) {
  const [hoverValue, setHoverValue] = useState<number>(0);
  const isInteractive = !readonly && !!onChange;
  const displayValue = isInteractive && hoverValue > 0 ? hoverValue : value;

  return (
    <div
      className={cn('inline-flex items-center', gapClasses[size])}
      role={isInteractive ? 'radiogroup' : 'img'}
      aria-label={
        isInteractive
          ? '별점 선택'
          : `${value}점 (5점 만점)`
      }
    >
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = star <= displayValue;

        if (isInteractive) {
          return (
            <button
              key={star}
              type="button"
              role="radio"
              aria-checked={star === value}
              aria-label={`${star}점`}
              className={cn(
                'inline-flex cursor-pointer items-center justify-center rounded-sm transition-colors',
                'min-h-[44px] min-w-[44px]',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              )}
              onClick={() => onChange(star)}
              onMouseEnter={() => setHoverValue(star)}
              onMouseLeave={() => setHoverValue(0)}
            >
              <Star
                className={cn(
                  sizeClasses[size],
                  'transition-colors',
                  filled
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'fill-none text-muted-foreground/40',
                )}
                aria-hidden="true"
              />
            </button>
          );
        }

        return (
          <Star
            key={star}
            className={cn(
              sizeClasses[size],
              filled
                ? 'fill-yellow-400 text-yellow-400'
                : 'fill-none text-muted-foreground/40',
            )}
            aria-hidden="true"
          />
        );
      })}
    </div>
  );
}
