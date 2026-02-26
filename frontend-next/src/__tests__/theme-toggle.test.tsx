import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';

// Track theme state outside the mock
const mockState = { theme: 'light', setTheme: vi.fn() };

vi.mock('next-themes', () => ({
  useTheme: () => mockState,
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Must import AFTER vi.mock
import { ThemeToggle } from '@/components/theme-toggle';

describe('ThemeToggle', () => {
  beforeEach(() => {
    cleanup();
    mockState.setTheme = vi.fn();
  });

  it('renders toggle button', () => {
    mockState.theme = 'light';
    render(<ThemeToggle />);
    expect(screen.getByRole('button', { name: '테마 변경' })).toBeInTheDocument();
  });

  it('toggles from light to dark', () => {
    mockState.theme = 'light';
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole('button', { name: '테마 변경' }));
    expect(mockState.setTheme).toHaveBeenCalledWith('dark');
  });

  it('toggles from dark to light', () => {
    mockState.theme = 'dark';
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole('button', { name: '테마 변경' }));
    expect(mockState.setTheme).toHaveBeenCalledWith('light');
  });
});
