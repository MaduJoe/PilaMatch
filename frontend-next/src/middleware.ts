import { NextRequest, NextResponse } from 'next/server';

const PUBLIC_PATHS = ['/login', '/signup', '/api/auth'];
const EXACT_PUBLIC_PATHS = ['/', '/terms', '/privacy', '/refund'];
const AUTH_PATHS = ['/login', '/signup'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('access_token')?.value;

  // Skip API routes except auth BFF
  if (pathname.startsWith('/api/') && !pathname.startsWith('/api/auth')) {
    // Inject Authorization header for proxied API requests
    if (token) {
      const headers = new Headers(request.headers);
      headers.set('Authorization', `Bearer ${token}`);
      return NextResponse.next({
        request: { headers },
      });
    }
    return NextResponse.next();
  }

  // Allow public paths without auth
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p)) || EXACT_PUBLIC_PATHS.includes(pathname)) {
    // Redirect authenticated users away from auth pages
    if (token && AUTH_PATHS.some((p) => pathname.startsWith(p))) {
      return NextResponse.redirect(new URL('/steps/profile', request.url));
    }
    return NextResponse.next();
  }

  // Protect /steps/* routes
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
