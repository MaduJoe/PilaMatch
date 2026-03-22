'use client';

import { useState, useEffect } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GeolocationState {
  latitude: number | null;
  longitude: number | null;
  error: string | null;
  loading: boolean;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Browser GPS 좌표를 1회 요청하는 훅.
 * 권한 거부 시 error를 설정하고 나머지는 null (graceful degradation).
 */
export function useGeolocation(): GeolocationState {
  const [state, setState] = useState<GeolocationState>({
    latitude: null,
    longitude: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    // SSR 또는 geolocation 미지원 브라우저
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setState({
        latitude: null,
        longitude: null,
        error: '이 브라우저에서는 위치 서비스를 사용할 수 없습니다.',
        loading: false,
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          error: null,
          loading: false,
        });
      },
      (positionError) => {
        let message: string;
        switch (positionError.code) {
          case positionError.PERMISSION_DENIED:
            message = '위치 권한이 거부되었습니다.';
            break;
          case positionError.POSITION_UNAVAILABLE:
            message = '위치 정보를 가져올 수 없습니다.';
            break;
          case positionError.TIMEOUT:
            message = '위치 요청 시간이 초과되었습니다.';
            break;
          default:
            message = '위치를 확인할 수 없습니다.';
        }
        setState({
          latitude: null,
          longitude: null,
          error: message,
          loading: false,
        });
      },
      {
        enableHighAccuracy: false, // 배터리 절약
        timeout: 10_000,
        maximumAge: 300_000, // 5분 캐시
      },
    );
  }, []);

  return state;
}
