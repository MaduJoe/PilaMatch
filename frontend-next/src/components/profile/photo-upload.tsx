'use client';

import { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Camera, Trash2, Loader2 } from 'lucide-react';

interface PhotoUploadProps {
  currentPhotoUrl?: string | null;
  onUploaded?: (url: string) => void;
  onRemoved?: () => void;
}

export function PhotoUpload({
  currentPhotoUrl,
  onUploaded,
  onRemoved,
}: PhotoUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(currentPhotoUrl ?? null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);

    // Upload
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/profiles/photo', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      onUploaded?.(data.photo_url);
    } catch {
      // Keep preview on error - user can retry
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    setPreview(null);
    onRemoved?.();
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-24 w-24">
        <div className="h-24 w-24 overflow-hidden rounded-full border-2 border-border bg-muted">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={preview}
              alt="프로필 사진"
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-3xl text-muted-foreground">
              <Camera className="h-8 w-8" />
            </div>
          )}
        </div>
        {isUploading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
            <Loader2 className="h-6 w-6 animate-spin text-white" />
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          <Camera className="mr-1 h-3 w-3" />
          {preview ? '변경' : '업로드'}
        </Button>
        {preview && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleRemove}
            disabled={isUploading}
          >
            <Trash2 className="mr-1 h-3 w-3" />
            삭제
          </Button>
        )}
      </div>
    </div>
  );
}
