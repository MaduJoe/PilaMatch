'use client';

import type { ContractResponse } from '@/lib/api-types';
import { useAuthStore } from '@/stores/auth-store';
import {
  formatCurrency,
  formatDate,
  formatTime,
  getContractStatusDisplay,
} from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SigningSection } from './signing-section';
import { InProgressSection } from './in-progress-section';
import { ContractPaymentSection } from './contract-payment-section';
import { CompletionConfirmSection } from './completion-confirm-section';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ContractCardProps {
  contract: ContractResponse;
  onAction: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function calcDurationMinutes(startTime: string, endTime: string): number {
  const [sh, sm] = startTime.split(':').map(Number);
  const [eh, em] = endTime.split(':').map(Number);
  return eh * 60 + em - (sh * 60 + sm);
}

function formatDuration(minutes: number): string {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}시간 ${mins}분` : `${hours}시간`;
  }
  return `${minutes}분`;
}

function statusBadgeVariant(
  status: string,
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'in_progress':
      return 'default';
    case 'completed':
      return 'default';
    case 'cancelled':
      return 'destructive';
    case 'pending_completion':
      return 'secondary';
    default:
      return 'outline';
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ContractCard({ contract, onAction }: ContractCardProps) {
  const user = useAuthStore((s) => s.user);
  const userRole = user?.role ?? 'instructor';
  const userId = user?.id ?? '';

  const statusDisplay = getContractStatusDisplay(contract.status);
  const isInstructor = userRole === 'instructor';
  const partnerName = isInstructor
    ? contract.studio_name ?? '스튜디오'
    : contract.instructor_name ?? '강사';
  const duration = calcDurationMinutes(contract.start_time, contract.end_time);

  return (
    <Card className="transition-shadow hover:shadow-md">
      {/* Header: partner name + date + status */}
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <CardTitle className="truncate text-base">{partnerName}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              {formatDate(contract.date)} {formatTime(contract.start_time)}-
              {formatTime(contract.end_time)}
            </p>
          </div>
          <Badge variant={statusBadgeVariant(contract.status)}>
            {statusDisplay.emoji} {statusDisplay.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Detail grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div>
            <span className="text-muted-foreground">수업 시간</span>
            <p className="font-medium">{formatDuration(duration)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">
              {isInstructor ? '스튜디오' : '강사'}
            </span>
            <p className="font-medium">{partnerName}</p>
          </div>
          <div>
            <span className="text-muted-foreground">시급</span>
            <p className="font-medium">{formatCurrency(contract.hourly_rate)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">총 금액</span>
            <p className="font-medium">
              {formatCurrency(contract.total_amount)}
            </p>
          </div>
        </div>

        {/* Status-specific section */}
        {contract.status === 'confirmed' && (
          <SigningSection
            contract={contract}
            userRole={userRole}
            onAction={onAction}
          />
        )}

        {contract.status === 'in_progress' && (
          <div className="space-y-4">
            <InProgressSection
              contract={contract}
              userRole={userRole}
              userId={userId}
              onAction={onAction}
            />
            {userRole === 'studio' && (
              <ContractPaymentSection
                contract={contract}
                onAction={onAction}
              />
            )}
          </div>
        )}

        {contract.status === 'pending_completion' && (
          <CompletionConfirmSection
            contract={contract}
            userRole={userRole}
            onAction={onAction}
          />
        )}
      </CardContent>
    </Card>
  );
}
