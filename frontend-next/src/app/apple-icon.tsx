import { ImageResponse } from 'next/og';

export const size = { width: 180, height: 180 };
export const contentType = 'image/png';

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
          borderRadius: '36px',
        }}
      >
        <span style={{ fontSize: 100, color: 'white', fontWeight: 700 }}>P</span>
      </div>
    ),
    { ...size },
  );
}
