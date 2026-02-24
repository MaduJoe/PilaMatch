'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { CreditCard, Building2 } from 'lucide-react';

interface PaymentMethodSelectorProps {
  isLoading?: boolean;
  onSelect: (method: 'card' | 'bank_transfer') => void;
}

export function PaymentMethodSelector({
  isLoading,
  onSelect,
}: PaymentMethodSelectorProps) {
  const [selected, setSelected] = useState<'card' | 'bank_transfer' | null>(null);

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">결제 수단 선택</p>
      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 text-sm transition-colors ${
            selected === 'card'
              ? 'border-primary bg-primary/5'
              : 'border-muted hover:border-muted-foreground/30'
          }`}
          onClick={() => setSelected('card')}
        >
          <CreditCard className="h-6 w-6" />
          <span className="font-medium">카드 자동결제</span>
          <span className="text-xs text-green-600 font-medium">추천</span>
        </button>
        <button
          type="button"
          className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 text-sm transition-colors ${
            selected === 'bank_transfer'
              ? 'border-primary bg-primary/5'
              : 'border-muted hover:border-muted-foreground/30'
          }`}
          onClick={() => setSelected('bank_transfer')}
        >
          <Building2 className="h-6 w-6" />
          <span className="font-medium">무통장입금</span>
          <span className="text-xs text-muted-foreground">1회</span>
        </button>
      </div>
      <Button
        className="min-h-[44px] w-full"
        disabled={!selected || isLoading}
        onClick={() => selected && onSelect(selected)}
      >
        {isLoading ? '처리 중...' : '결제 진행'}
      </Button>
    </div>
  );
}
