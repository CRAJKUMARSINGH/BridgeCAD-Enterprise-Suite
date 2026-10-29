import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Vitest runs without `globals: true`, so Testing Library's auto-cleanup does
// not register itself; unmount rendered trees explicitly between tests.
afterEach(() => {
  cleanup()
})
