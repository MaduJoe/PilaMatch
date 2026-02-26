import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import GlobalError from '@/app/error';
import NotFound from '@/app/not-found';
import Loading from '@/app/loading';

describe('Error Boundary', () => {
  it('renders error message', () => {
    const error = new Error('Test error');
    const reset = vi.fn();
    render(<GlobalError error={error} reset={reset} />);

    expect(screen.getByText('문제가 발생했습니다')).toBeInTheDocument();
    expect(screen.getByText(/일시적인 오류/)).toBeInTheDocument();
  });

  it('calls reset on retry click', () => {
    const error = new Error('Test error');
    const reset = vi.fn();
    const { container } = render(<GlobalError error={error} reset={reset} />);

    // shadcn Button renders <button data-slot="button">
    const retryBtn = container.querySelector('button[data-slot="button"]');
    expect(retryBtn).toBeTruthy();
    fireEvent.click(retryBtn!);
    expect(reset).toHaveBeenCalledOnce();
  });

  it('has home link', () => {
    const error = new Error('Test error');
    const reset = vi.fn();
    const { container } = render(<GlobalError error={error} reset={reset} />);

    const homeLinks = container.querySelectorAll('a[href="/"]');
    expect(homeLinks.length).toBeGreaterThan(0);
  });
});

describe('404 Page', () => {
  it('renders not found message', () => {
    render(<NotFound />);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('페이지를 찾을 수 없습니다')).toBeInTheDocument();
  });

  it('has home link', () => {
    const { container } = render(<NotFound />);
    const homeLinks = container.querySelectorAll('a[href="/"]');
    expect(homeLinks.length).toBeGreaterThan(0);
  });
});

describe('Loading Page', () => {
  it('renders loading spinner', () => {
    render(<Loading />);
    expect(screen.getByText('로딩 중...')).toBeInTheDocument();
  });
});
