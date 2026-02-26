import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PhotoUpload } from '@/components/profile/photo-upload';

describe('PhotoUpload', () => {
  it('renders upload button when no photo', () => {
    render(<PhotoUpload />);
    expect(screen.getByText('업로드')).toBeInTheDocument();
  });

  it('renders change and delete buttons when photo exists', () => {
    render(<PhotoUpload currentPhotoUrl="https://example.com/photo.jpg" />);
    expect(screen.getByText('변경')).toBeInTheDocument();
    expect(screen.getByText('삭제')).toBeInTheDocument();
  });

  it('shows image preview when photo URL provided', () => {
    render(<PhotoUpload currentPhotoUrl="https://example.com/photo.jpg" />);
    const img = screen.getByAltText('프로필 사진');
    expect(img).toHaveAttribute('src', 'https://example.com/photo.jpg');
  });

  it('calls onRemoved when delete clicked', async () => {
    const onRemoved = vi.fn();
    render(
      <PhotoUpload
        currentPhotoUrl="https://example.com/photo.jpg"
        onRemoved={onRemoved}
      />,
    );
    const deleteBtn = screen.getByRole('button', { name: /삭제/ });
    fireEvent.click(deleteBtn);
    expect(onRemoved).toHaveBeenCalledOnce();
  });

  it('has hidden file input', () => {
    render(<PhotoUpload />);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeTruthy();
    expect(fileInput.accept).toBe('image/*');
    expect(fileInput.className).toContain('hidden');
  });
});
