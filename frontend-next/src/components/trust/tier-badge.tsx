'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface TierBadgeProps {
  tier: string;
  label?: string;
  size?: 'sm' | 'md';
}

const TIER_COLORS: Record<string, string> = {
  t1_basic: 'bg-gray-100 text-gray-700 border-gray-300',
  t2_verified: 'bg-blue-100 text-blue-700 border-blue-300',
  t3_pro: 'bg-amber-100 text-amber-700 border-amber-300',
  c1_basic: 'bg-gray-100 text-gray-700 border-gray-300',
  c2_verified: 'bg-blue-100 text-blue-700 border-blue-300',
};

const TIER_LABELS: Record<string, string> = {
  t1_basic: 'Basic',
  t2_verified: 'Verified',
  t3_pro: 'Pro',
  c1_basic: 'Basic',
  c2_verified: 'Verified',
};

export function TierBadge({ tier, label, size = 'sm' }: TierBadgeProps) {
  const colorClass = TIER_COLORS[tier] ?? TIER_COLORS.t1_basic;
  const displayLabel = label ?? TIER_LABELS[tier] ?? 'Basic';

  return (
    <Badge
      variant="outline"
      className={cn(
        colorClass,
        size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1',
      )}
    >
      {displayLabel}
    </Badge>
  );
}
