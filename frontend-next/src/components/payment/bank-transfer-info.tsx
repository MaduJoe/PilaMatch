'use client';

import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';

interface BankTransferInfoProps {
  bankName: string;
  accountNumber: string;
  accountHolder: string;
  amount: number;
  depositorName: string;
  expiresAt: string;
  orderId: string;
}

export function BankTransferInfo({
  bankName,
  accountNumber,
  accountHolder,
  amount,
  depositorName,
  expiresAt,
  orderId,
}: BankTransferInfoProps) {
  const isExpired = new Date(expiresAt) < new Date();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">주문번호: {orderId}</span>
        <Badge variant={isExpired ? 'destructive' : 'secondary'}>
          {isExpired ? '만료' : '입금 대기중'}
        </Badge>
      </div>

      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">은행</span>
          <span className="font-medium">{bankName}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">계좌번호</span>
          <span className="font-medium font-mono">{accountNumber}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">예금주</span>
          <span className="font-medium">{accountHolder}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">입금액</span>
          <span className="text-lg font-bold">{formatCurrency(amount)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">입금자명</span>
          <span className="font-medium">{depositorName}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">입금기한</span>
          <span className="font-medium">
            {new Date(expiresAt).toLocaleString('ko-KR')}
          </span>
        </div>
      </div>

      <div className="rounded-lg bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 p-3">
        <p className="text-xs text-yellow-800 dark:text-yellow-200">
          반드시 <strong>{depositorName}</strong> 명의로 입금해주세요. 입금자명이 다르면 확인이 지연될 수 있습니다.
        </p>
      </div>
    </div>
  );
}
