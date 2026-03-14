'use client';

import { useState, useCallback } from 'react';
import { CATEGORIES, REGION_NAMES } from '@/lib/constants';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronUp, Check } from 'lucide-react';

// ---------------------------------------------------------------------------
// Region groups (same as instructor-profile-form.tsx)
// ---------------------------------------------------------------------------

const REGION_GROUPS: Record<string, string[]> = {
  '강남권': ['강남구', '서초구', '송파구', '강동구'],
  '마용성': ['마포구', '용산구', '성동구'],
  '동북권': ['광진구', '동대문구', '중랑구', '성북구', '강북구', '도봉구', '노원구'],
  '서북권': ['은평구', '서대문구', '종로구', '중구'],
  '서남권': ['영등포구', '동작구', '관악구', '금천구', '구로구', '양천구', '강서구'],
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface JobFilters {
  category: string;
  regions: string[];
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
  const [regionOpen, setRegionOpen] = useState(false);

  const selectedRegions = filters.regions;
  const allSelected = REGION_NAMES.length > 0 && REGION_NAMES.every((r) => selectedRegions.includes(r));

  const setRegions = useCallback(
    (regions: string[]) => {
      onChange({ ...filters, regions });
    },
    [filters, onChange],
  );

  const handleSelectAll = useCallback(() => {
    setRegions(allSelected ? [] : [...REGION_NAMES]);
  }, [allSelected, setRegions]);

  const handleGroupToggle = useCallback(
    (groupRegions: string[]) => {
      const allGroupSelected = groupRegions.every((r) => selectedRegions.includes(r));
      if (allGroupSelected) {
        setRegions(selectedRegions.filter((r) => !groupRegions.includes(r)));
      } else {
        setRegions(Array.from(new Set([...selectedRegions, ...groupRegions])));
      }
    },
    [selectedRegions, setRegions],
  );

  const handleRegionToggle = useCallback(
    (region: string) => {
      if (selectedRegions.includes(region)) {
        setRegions(selectedRegions.filter((r) => r !== region));
      } else {
        setRegions([...selectedRegions, region]);
      }
    },
    [selectedRegions, setRegions],
  );

  const regionLabel =
    selectedRegions.length === 0
      ? '지역 전체'
      : selectedRegions.length <= 2
        ? selectedRegions.join(', ')
        : `${selectedRegions[0]} 외 ${selectedRegions.length - 1}곳`;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* Category toggle */}
        <ToggleGroup
          type="single"
          variant="outline"
          value={filters.category}
          onValueChange={(value) => {
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

        {/* Region toggle button */}
        <Button
          variant={selectedRegions.length > 0 ? 'default' : 'outline'}
          size="sm"
          className="min-h-[44px] gap-1.5"
          onClick={() => setRegionOpen(!regionOpen)}
          aria-expanded={regionOpen}
          aria-label="지역 필터"
        >
          {regionLabel}
          {regionOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
        </Button>

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
      </div>

      {/* Grouped regions panel (collapsible) */}
      {regionOpen && (
        <div className="rounded-xl border border-border/60 bg-muted/20 p-3 space-y-2.5">
          {/* Select all */}
          <button
            type="button"
            className={`flex items-center gap-1.5 text-xs font-semibold transition-colors ${
              allSelected ? 'text-primary' : 'text-foreground/70 hover:text-primary'
            }`}
            onClick={handleSelectAll}
          >
            <span
              className={`flex size-4 items-center justify-center rounded border text-[10px] transition-colors ${
                allSelected
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border'
              }`}
            >
              {allSelected && '✓'}
            </span>
            서울 전체
          </button>

          {/* Groups */}
          {Object.entries(REGION_GROUPS).map(([groupName, groupRegions]) => {
            const groupAllSelected = groupRegions.every((r) => selectedRegions.includes(r));
            const groupSomeSelected = groupRegions.some((r) => selectedRegions.includes(r));
            return (
              <div key={groupName}>
                <button
                  type="button"
                  className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-foreground/80 hover:text-primary transition-colors"
                  onClick={() => handleGroupToggle(groupRegions)}
                >
                  <span
                    className={`flex size-4 items-center justify-center rounded border text-[10px] transition-colors ${
                      groupAllSelected
                        ? 'border-primary bg-primary text-primary-foreground'
                        : groupSomeSelected
                          ? 'border-primary/50 bg-primary/10'
                          : 'border-border'
                    }`}
                  >
                    {groupAllSelected && '✓'}
                  </span>
                  {groupName}
                </button>
                <div className="flex flex-wrap gap-1.5 pl-5">
                  {groupRegions.map((region) => {
                    const isSelected = selectedRegions.includes(region);
                    return (
                      <button
                        key={region}
                        type="button"
                        className={`rounded-lg px-2.5 py-1 text-xs transition-all ${
                          isSelected
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'bg-background border border-border/60 text-muted-foreground hover:border-primary/40'
                        }`}
                        onClick={() => handleRegionToggle(region)}
                      >
                        {region}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}

          {/* Clear */}
          {selectedRegions.length > 0 && (
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-destructive transition-colors"
              onClick={() => setRegions([])}
            >
              선택 초기화
            </button>
          )}
        </div>
      )}
    </div>
  );
}
