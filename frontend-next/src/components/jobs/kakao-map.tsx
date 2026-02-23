'use client';

import { useEffect, useRef, useState } from 'react';
import { SEOUL_REGIONS } from '@/lib/constants';

// Declare kakao global to avoid TypeScript errors with the SDK
declare global {
  interface Window {
    kakao: any;
  }
}

interface KakaoMapProps {
  region: string;
  height?: number;
}

const KAKAO_MAP_KEY = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY;

/**
 * Loads the Kakao Maps SDK script once globally.
 * Returns a promise that resolves when the SDK is ready.
 */
let sdkLoadPromise: Promise<void> | null = null;

function loadKakaoSDK(): Promise<void> {
  if (sdkLoadPromise) return sdkLoadPromise;

  sdkLoadPromise = new Promise<void>((resolve, reject) => {
    // Already loaded
    if (window.kakao?.maps) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_MAP_KEY}&autoload=false`;
    script.async = true;

    script.onload = () => {
      window.kakao.maps.load(() => {
        resolve();
      });
    };

    script.onerror = () => {
      sdkLoadPromise = null;
      reject(new Error('Kakao Maps SDK failed to load'));
    };

    document.head.appendChild(script);
  });

  return sdkLoadPromise;
}

export function KakaoMap({ region, height = 300 }: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const [sdkReady, setSdkReady] = useState(false);
  const [sdkError, setSdkError] = useState(false);

  const coords = SEOUL_REGIONS[region];

  // Load the SDK on mount
  useEffect(() => {
    if (!KAKAO_MAP_KEY) return;

    loadKakaoSDK()
      .then(() => setSdkReady(true))
      .catch(() => setSdkError(true));
  }, []);

  // Create or update the map when SDK is ready or region changes
  useEffect(() => {
    if (!sdkReady || !containerRef.current || !coords) return;

    const kakao = window.kakao;
    const position = new kakao.maps.LatLng(coords.lat, coords.lng);

    if (!mapRef.current) {
      // Create map for the first time
      const map = new kakao.maps.Map(containerRef.current, {
        center: position,
        level: 5,
      });
      mapRef.current = map;

      const marker = new kakao.maps.Marker({ position });
      marker.setMap(map);
      markerRef.current = marker;

      const infowindow = new kakao.maps.InfoWindow({
        content: `<div style="padding:4px 8px;font-size:13px;white-space:nowrap;">${region}</div>`,
      });
      infowindow.open(map, marker);
    } else {
      // Update existing map position
      mapRef.current.setCenter(position);

      if (markerRef.current) {
        markerRef.current.setPosition(position);
      }

      // Re-create infowindow with new region name
      const infowindow = new kakao.maps.InfoWindow({
        content: `<div style="padding:4px 8px;font-size:13px;white-space:nowrap;">${region}</div>`,
      });
      infowindow.open(mapRef.current, markerRef.current);
    }
  }, [sdkReady, region, coords]);

  // Fallback: no API key configured
  if (!KAKAO_MAP_KEY || sdkError) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 bg-muted/50 text-sm text-muted-foreground"
        style={{ height }}
        role="img"
        aria-label={`선택된 지역: ${region}`}
      >
        선택된 지역: {region}
      </div>
    );
  }

  // Region not found in SEOUL_REGIONS
  if (!coords) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border-2 border-dashed border-yellow-400/50 bg-yellow-50 text-sm text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400"
        style={{ height }}
        role="alert"
      >
        지역 &quot;{region}&quot;의 좌표 정보가 없습니다
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full rounded-lg overflow-hidden border"
      style={{ height }}
      aria-label={`${region} 지도`}
    />
  );
}
