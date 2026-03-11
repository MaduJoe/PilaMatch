'use client';

import { useRef, useState } from 'react';
import type { TierResponse } from '@/lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { HelpCircle, Upload, FileCheck, X } from 'lucide-react';
import { TierBadge } from './tier-badge';
import { toast } from 'sonner';

const TIER_BENEFITS = [
  { tier: 'Basic', daily: '하루 2회', region: '홈 + 1곳', urgent: '긴급 1건' },
  { tier: 'Verified', daily: '하루 3회', region: '홈 + 2곳', urgent: '긴급 2건' },
  { tier: 'Premium', daily: '무제한', region: '전체', urgent: '무제한' },
];

interface TierCardProps {
  data: TierResponse;
}

export function TierCard({ data }: TierCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newFileNames: string[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      // Validate file type (images and PDFs only)
      if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
        toast.error('이미지 또는 PDF 파일만 업로드할 수 있습니다');
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error('파일 크기는 10MB 이하만 가능합니다');
        continue;
      }
      newFileNames.push(file.name);
    }

    if (newFileNames.length > 0) {
      setUploadedFiles((prev) => [...prev, ...newFileNames]);
      toast.success(`${newFileNames.length}개 파일이 첨부되었습니다`);
    }

    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="font-display text-lg tracking-tight">내 등급</CardTitle>
            <TierBadge tier={data.tier} label={data.tier_label} size="md" />
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-muted-foreground hover:text-foreground transition-colors" aria-label="등급 혜택 보기">
                <HelpCircle className="size-4" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-4" side="bottom" align="end">
              <p className="font-display text-xs font-semibold mb-3 tracking-wide uppercase text-muted-foreground">등급별 혜택</p>
              <div className="space-y-3">
                {TIER_BENEFITS.map((b) => (
                  <div key={b.tier} className="space-y-1">
                    <p className="font-display text-xs font-semibold">{b.tier}</p>
                    <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground">
                      <span>지원</span><span>{b.daily}</span>
                      <span>지역</span><span>{b.region}</span>
                      <span>긴급</span><span>{b.urgent}</span>
                    </div>
                  </div>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {/* Stats grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className="font-display text-xl font-bold">{data.completed_jobs_recent}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">완료</p>
          </div>
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className="font-display text-xl font-bold">{data.no_show_recent}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">노쇼</p>
          </div>
          <div className="rounded-xl bg-muted/50 p-3 text-center">
            <p className={`font-display text-xl font-bold ${data.same_day_cancel_recent > 0 ? 'text-urgent' : ''}`}>
              {data.same_day_cancel_recent + data.late_recent}
            </p>
            <p className="text-[10px] text-muted-foreground mt-0.5">이슈</p>
          </div>
        </div>

        {/* Certificate upload section */}
        <div className="rounded-xl border border-dashed border-primary/30 bg-primary/[0.03] p-4">
          <p className="text-sm font-semibold mb-1">자격증 첨부</p>
          <p className="text-xs text-muted-foreground mb-3">
            자격증을 첨부하면 <span className="font-medium text-primary">Verified 등급</span>으로 승급할 수 있습니다
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf"
            multiple
            className="hidden"
            onChange={handleFileSelect}
          />

          {uploadedFiles.length > 0 && (
            <div className="mb-3 space-y-1.5">
              {uploadedFiles.map((name, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-lg bg-background px-3 py-1.5 text-xs"
                >
                  <FileCheck className="size-3.5 shrink-0 text-green-600" />
                  <span className="flex-1 truncate">{name}</span>
                  <button
                    type="button"
                    className="text-muted-foreground hover:text-red-500 transition-colors"
                    onClick={() => removeFile(i)}
                    aria-label={`${name} 삭제`}
                  >
                    <X className="size-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-full border-primary/30 text-primary hover:bg-primary/5"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mr-1.5 size-4" />
            자격증 파일 선택
          </Button>

          {uploadedFiles.length > 0 && (
            <Button
              type="button"
              size="sm"
              className="w-full mt-2"
              onClick={() => {
                toast.info('자격증 검토 요청이 접수되었습니다. 심사 후 등급이 변경됩니다.');
                setUploadedFiles([]);
              }}
            >
              제출하기
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
