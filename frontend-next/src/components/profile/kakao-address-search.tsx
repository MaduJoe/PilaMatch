'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Search, Loader2, PenLine } from 'lucide-react';
import { Input } from '@/components/ui/input';
import api from '@/lib/api-client';
import { REGION_NAMES } from '@/lib/constants';

interface KakaoPlace {
  place_name: string;
  address_name: string;
  road_address_name: string;
  region: string;
  latitude: number;
  longitude: number;
  phone: string;
}

interface SelectedPlace {
  address: string;
  region: string;
  latitude?: number;
  longitude?: number;
  phone?: string;
}

interface KakaoAddressSearchProps {
  /** 현재 주소 값 (제어 컴포넌트) */
  value?: string;
  /** 현재 지역 값 (직접 입력 모드 초기값) */
  regionValue?: string;
  /** 장소 선택 또는 직접 입력 완료 시 콜백 */
  onSelect: (place: SelectedPlace) => void;
  placeholder?: string;
}

function useDebounce(value: string, delay: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export function KakaoAddressSearch({
  value = '',
  regionValue = '',
  onSelect,
  placeholder = '스튜디오명 또는 주소 검색',
}: KakaoAddressSearchProps) {
  const [inputValue, setInputValue] = useState(value);
  const [isOpen, setIsOpen] = useState(false);
  const [manualMode, setManualMode] = useState(false);
  const [manualRegion, setManualRegion] = useState(regionValue);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const debouncedQuery = useDebounce(inputValue, 300);

  // Sync external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);
  useEffect(() => {
    setManualRegion(regionValue);
  }, [regionValue]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { data, isFetching, isError } = useQuery({
    queryKey: ['kakao-search', debouncedQuery],
    queryFn: () => api.kakao.search(debouncedQuery),
    enabled: !manualMode && debouncedQuery.length >= 2,
    staleTime: 30_000,
    retry: 1,
  });

  const handleSelect = useCallback(
    (place: KakaoPlace) => {
      const address = place.road_address_name || place.address_name;
      setInputValue(address);
      setIsOpen(false);
      setManualMode(false);
      onSelect({
        address,
        region: place.region,
        latitude: place.latitude,
        longitude: place.longitude,
        phone: place.phone || undefined,
      });
    },
    [onSelect],
  );

  const switchToManual = useCallback(() => {
    setManualMode(true);
    setIsOpen(false);
  }, []);

  const switchToSearch = useCallback(() => {
    setManualMode(false);
    setInputValue('');
    setManualRegion('');
  }, []);

  // In manual mode, propagate changes on blur
  const handleManualBlur = useCallback(() => {
    if (manualMode && inputValue.trim()) {
      onSelect({
        address: inputValue.trim(),
        region: manualRegion,
      });
    }
  }, [manualMode, inputValue, manualRegion, onSelect]);

  const results = data?.results ?? [];
  const showNoResults = isOpen && debouncedQuery.length >= 2 && !isFetching && results.length === 0;

  // ---------- Manual input mode ----------
  if (manualMode) {
    return (
      <div className="space-y-2">
        <div>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onBlur={handleManualBlur}
            placeholder="서울시 강남구 테헤란로 123"
            className="min-h-[44px]"
          />
        </div>
        <div>
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={manualRegion}
            onChange={(e) => {
              setManualRegion(e.target.value);
              onSelect({
                address: inputValue.trim(),
                region: e.target.value,
              });
            }}
          >
            <option value="">지역 선택</option>
            {REGION_NAMES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="flex items-center gap-1.5 text-xs text-primary hover:underline"
          onClick={switchToSearch}
        >
          <Search className="size-3" />
          검색으로 돌아가기
        </button>
      </div>
    );
  }

  // ---------- Search mode ----------
  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => {
            if (debouncedQuery.length >= 2) setIsOpen(true);
          }}
          placeholder={placeholder}
          className="min-h-[44px] pl-9 pr-9"
        />
        {isFetching && (
          <Loader2 className="absolute right-3 top-1/2 size-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {isOpen && results.length > 0 && (
        <ul className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-xl border bg-popover shadow-lg">
          {results.map((place, idx) => (
            <li key={`${place.latitude}-${place.longitude}-${idx}`}>
              <button
                type="button"
                className="flex w-full items-start gap-3 px-3 py-2.5 text-left transition-colors hover:bg-accent"
                onClick={() => handleSelect(place)}
              >
                <MapPin className="mt-0.5 size-4 shrink-0 text-primary" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{place.place_name}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {place.road_address_name || place.address_name}
                  </p>
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}

      {(showNoResults || isError) && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border bg-popover p-3 shadow-lg">
          <p className="text-center text-sm text-muted-foreground">
            {isError ? '검색 서비스에 연결할 수 없습니다' : '검색 결과가 없습니다'}
          </p>
          <button
            type="button"
            className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            onClick={switchToManual}
          >
            <PenLine className="size-3.5" />
            직접 입력
          </button>
        </div>
      )}
    </div>
  );
}
