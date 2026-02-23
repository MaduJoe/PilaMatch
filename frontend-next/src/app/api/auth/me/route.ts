import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;

  if (!token) {
    return NextResponse.json(
      { detail: { code: 'NOT_AUTHENTICATED', message: '인증이 필요합니다' } },
      { status: 401 },
    );
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      // If token is invalid, clear the cookie
      if (res.status === 401) {
        const response = NextResponse.json(error, { status: 401 });
        response.cookies.delete('access_token');
        return response;
      }
      return NextResponse.json(error, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: { code: 'SERVER_ERROR', message: '서버 오류가 발생했습니다' } },
      { status: 500 },
    );
  }
}
