import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FileDropzone from './FileDropzone'

describe('FileDropzone', () => {
  it('shows the placeholder label when no file is selected', () => {
    render(<FileDropzone onFile={vi.fn()} label="Drop here" />)
    expect(screen.getByText('Drop here')).toBeInTheDocument()
  })

  it('shows the file name supplied by the parent page', () => {
    const file = new File(['x'], 'bridge.xlsx')
    render(<FileDropzone onFile={vi.fn()} file={file} />)
    expect(screen.getByText(/bridge\.xlsx/)).toBeInTheDocument()
  })

  it('does not leak another page’s file: no file prop means placeholder', () => {
    render(<FileDropzone onFile={vi.fn()} label="Drop here" file={null} />)
    expect(screen.queryByText(/\.xlsx/)).toBeNull()
  })

  it('is keyboard operable — role=button, focusable, Enter opens the picker', () => {
    const { container } = render(<FileDropzone onFile={vi.fn()} />)
    const zone = screen.getByRole('button')
    expect(zone).toHaveAttribute('tabindex', '0')

    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    const click = vi.spyOn(input, 'click').mockImplementation(() => {})
    fireEvent.keyDown(zone, { key: 'Enter' })
    expect(click).toHaveBeenCalled()
  })

  it('calls onFile when a file is dropped', () => {
    const onFile = vi.fn()
    render(<FileDropzone onFile={onFile} />)
    const file = new File(['x'], 'drop.xlsx')
    fireEvent.drop(screen.getByRole('button'), { dataTransfer: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })

  it('calls onFile when a file is picked from the dialog', () => {
    const onFile = vi.fn()
    const { container } = render(<FileDropzone onFile={onFile} />)
    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    const file = new File(['x'], 'pick.xlsx')
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })
})
