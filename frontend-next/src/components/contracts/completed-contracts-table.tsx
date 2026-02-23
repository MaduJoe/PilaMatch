'use client';

import type { ContractResponse } from '@/lib/api-types';
import {
  formatCurrency,
  formatDate,
  formatTime,
  getContractStatusDisplay,
} from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CompletedContractsTableProps {
  contracts: ContractResponse[];
  userRole: string;
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
): 'default' | 'destructive' | 'outline' {
  if (status === 'completed') return 'default';
  if (status === 'cancelled') return 'destructive';
  return 'outline';
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompletedContractsTable({
  contracts,
  userRole,
}: CompletedContractsTableProps) {
  if (contracts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-20">
        <p className="text-sm text-muted-foreground">
          완료된 계약 내역이 없습니다
        </p>
      </div>
    );
  }

  const isInstructor = userRole === 'instructor';

  // Metrics
  const totalCount = contracts.length;
  const completedCount = contracts.filter((c) => c.status === 'completed').length;
  const cancelledCount = contracts.filter((c) => c.status === 'cancelled').length;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>상태</TableHead>
            <TableHead>상대방</TableHead>
            <TableHead>날짜</TableHead>
            <TableHead className="hidden sm:table-cell">클래스 시간</TableHead>
            <TableHead className="text-right">계약금액</TableHead>
            <TableHead className="hidden text-right sm:table-cell">
              정산금액
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {contracts.map((contract) => {
            const statusDisplay = getContractStatusDisplay(contract.status);
            const partnerName = isInstructor
              ? contract.studio_name ?? '스튜디오'
              : contract.instructor_name ?? '강사';
            const duration = calcDurationMinutes(
              contract.start_time,
              contract.end_time,
            );

            return (
              <TableRow key={contract.id}>
                <TableCell>
                  <Badge variant={statusBadgeVariant(contract.status)}>
                    {statusDisplay.emoji} {statusDisplay.label}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[120px] truncate font-medium">
                  {partnerName}
                </TableCell>
                <TableCell className="whitespace-nowrap text-sm">
                  {formatDate(contract.date)}
                </TableCell>
                <TableCell className="hidden whitespace-nowrap text-sm sm:table-cell">
                  {formatTime(contract.start_time)}-
                  {formatTime(contract.end_time)} ({formatDuration(duration)})
                </TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(contract.total_amount)}
                </TableCell>
                <TableCell className="hidden text-right sm:table-cell">
                  {contract.settlement_amount != null
                    ? formatCurrency(contract.settlement_amount)
                    : '-'}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {/* Summary metrics */}
      <div className="flex items-center justify-center gap-6 rounded-md border bg-muted/30 p-3 text-sm">
        <div className="text-center">
          <p className="text-muted-foreground">총 계약</p>
          <p className="font-bold">{totalCount}건</p>
        </div>
        <div className="text-center">
          <p className="text-muted-foreground">완료</p>
          <p className="font-bold text-green-600">{completedCount}건</p>
        </div>
        <div className="text-center">
          <p className="text-muted-foreground">취소</p>
          <p className="font-bold text-red-600">{cancelledCount}건</p>
        </div>
      </div>
    </div>
  );
}
