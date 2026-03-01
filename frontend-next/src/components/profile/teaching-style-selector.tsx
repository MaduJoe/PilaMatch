'use client';

import { STYLE_OPTIONS } from '@/lib/constants';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';

interface TeachingStyleSelectorProps {
  value: Record<string, string>;
  onChange: (style: Record<string, string>) => void;
  /** Which keys to show (default: all) */
  keys?: string[];
}

export function TeachingStyleSelector({
  value,
  onChange,
  keys,
}: TeachingStyleSelectorProps) {
  const styleKeys = keys ?? Object.keys(STYLE_OPTIONS);

  return (
    <div className="space-y-4">
      {styleKeys.map((key) => {
        const config = STYLE_OPTIONS[key as keyof typeof STYLE_OPTIONS];
        if (!config) return null;

        return (
          <div key={key} className="space-y-1.5">
            <label className="text-sm font-medium">{config.label}</label>
            <ToggleGroup
              type="single"
              value={value[key] ?? ''}
              onValueChange={(val) => {
                if (!val) return;
                onChange({ ...value, [key]: val });
              }}
              className="flex flex-wrap gap-1.5"
            >
              {config.options.map((opt) => (
                <ToggleGroupItem
                  key={opt.value}
                  value={opt.value}
                  aria-label={opt.label}
                  className="min-h-[40px] text-sm"
                >
                  {opt.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>
        );
      })}
    </div>
  );
}
