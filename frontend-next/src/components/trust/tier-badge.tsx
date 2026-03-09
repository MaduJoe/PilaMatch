'use client';

import { cn } from '@/lib/utils';

interface TierBadgeProps {
  tier: string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

const TIER_CONFIG: Record<string, { label: string; bg: string; text: string; border: string; icon: string }> = {
  t1_basic: {
    label: 'Basic',
    bg: 'bg-gray-100 dark:bg-gray-800/50',
    text: 'text-gray-600 dark:text-gray-400',
    border: 'border-gray-200 dark:border-gray-700',
    icon: '',
  },
  t2_verified: {
    label: 'Verified',
    bg: 'bg-primary/10 dark:bg-primary/15',
    text: 'text-primary dark:text-primary',
    border: 'border-primary/20 dark:border-primary/30',
    icon: '\u2713',
  },
  t3_pro: {
    label: 'Premium',
    bg: 'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-700',
    icon: '\u2605',
  },
  c1_basic: {
    label: 'Basic',
    bg: 'bg-gray-100 dark:bg-gray-800/50',
    text: 'text-gray-600 dark:text-gray-400',
    border: 'border-gray-200 dark:border-gray-700',
    icon: '',
  },
  c2_verified: {
    label: 'Verified',
    bg: 'bg-primary/10 dark:bg-primary/15',
    text: 'text-primary dark:text-primary',
    border: 'border-primary/20 dark:border-primary/30',
    icon: '\u2713',
  },
};

export function TierBadge({ tier, label, size = 'sm' }: TierBadgeProps) {
  const config = TIER_CONFIG[tier] ?? TIER_CONFIG.t1_basic;
  const displayLabel = label ?? config.label;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-0.5',
    md: 'text-xs px-2.5 py-1 gap-1',
    lg: 'text-sm px-3 py-1.5 gap-1',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-display font-semibold rounded-md border whitespace-nowrap shrink-0 tracking-wide uppercase',
        config.bg,
        config.text,
        config.border,
        sizeClasses[size],
      )}
    >
      {config.icon && (
        <span className="leading-none" aria-hidden="true">{config.icon}</span>
      )}
      {displayLabel}
    </span>
  );
}
