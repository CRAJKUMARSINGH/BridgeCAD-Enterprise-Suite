import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { SARASWATI } from './SaraswatiMascot'

describe('SARASWATI Component', () => {
  it('renders without crashing', () => {
    const { container } = render(<SARASWATI />)
    expect(container).toBeTruthy()
  })

  it('handles basic props correctly', () => {
    const { container } = render(<SARASWATI />)
    expect(container).toBeTruthy()
    const img = container.querySelector('img')
    expect(img).not.toBeNull()
    expect(img?.getAttribute('alt')).toBeTruthy()
  })

  it('matches snapshot', () => {
    const { container } = render(<SARASWATI />)
    expect(container.firstChild).toMatchSnapshot()
  })
})
