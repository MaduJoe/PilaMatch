'use client';

import { CATEGORIES, REGION_NAMES } from '@/lib/constants';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface JobFilters {
  category: string;
  region: string;
  sortByScore: boolean;
  urgentOnly: boolean;
}

interface JobFiltersProps {
  filters: JobFilters;
  onChange: (filters: JobFilters) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function JobFiltersBar({ filters, onChange }: JobFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Category toggle */}
      <ToggleGroup
        type="single"
        variant="outline"
        value={filters.category}
        onValueChange={(value) => {
          // When deselecting, fall back to "all"
          onChange({ ...filters, category: value || 'all' });
        }}
        aria-label="종목 필터"
      >
        <ToggleGroupItem value="all" aria-label="전체 종목">
          전체
        </ToggleGroupItem>
        {CATEGORIES.map((cat) => (
          <ToggleGroupItem key={cat.value} value={cat.value} aria-label={cat.label}>
            {cat.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      {/* Region select */}
      <Select
        value={filters.region}
        onValueChange={(value) => onChange({ ...filters, region: value })}
      >
        <SelectTrigger aria-label="지역 필터" className="w-[140px]">
          <SelectValue placeholder="지역 선택" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">전체</SelectItem>
          {REGION_NAMES.map((name) => (
            <SelectItem key={name} value={name}>
              {name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Urgent-only toggle */}
      <Button
        variant={filters.urgentOnly ? 'destructive' : 'outline'}
        size="sm"
        className="min-h-[44px]"
        onClick={() => onChange({ ...filters, urgentOnly: !filters.urgentOnly })}
        aria-label={filters.urgentOnly ? '긴급 필터 해제' : '긴급 공고만 보기'}
        aria-pressed={filters.urgentOnly}
      >
        {filters.urgentOnly ? '긴급만 ON' : '긴급만'}
      </Button>

      {/* Sort by matching score */}
      <div className="flex items-center gap-2">
        <Checkbox
          id="sort-by-score"
          checked={filters.sortByScore}
          onCheckedChange={(checked) =>
            onChange({ ...filters, sortByScore: checked === true })
          }
          aria-label="매칭 점수 순으로 정렬"
        />
        <Label htmlFor="sort-by-score" className="cursor-pointer text-sm">
          매칭순
        </Label>
      </div>
    </div>
  );
}
