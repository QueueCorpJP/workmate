import '@testing-library/jest-dom'
import { beforeAll, afterEach, afterAll } from 'vitest'
import { setupServer } from 'msw/node'
import { rest } from 'msw'

// Mock API handlers
const handlers = [
  rest.post('/api/login', (req, res, ctx) => {
    return res(
      ctx.json({
        user: {
          id: 'test-user-id',
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
          company_id: 'test-company'
        },
        token: 'mock-jwt-token'
      })
    )
  }),
  
  rest.post('/api/chat', (req, res, ctx) => {
    return res(
      ctx.json({
        response: 'こんにちは！テストメッセージの回答です。',
        sources: ['test-document.pdf'],
        category: 'greeting',
        sentiment: 'positive'
      })
    )
  }),

  rest.get('/api/chat-history/:companyId', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '1',
          user_message: 'テスト質問',
          bot_response: 'テスト回答',
          timestamp: '2023-01-01T00:00:00Z',
          category: 'test',
          sentiment: 'neutral'
        }
      ])
    )
  }),

  rest.post('/api/upload-document', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'uploaded-doc-id',
        name: 'test-document.pdf',
        message: 'ファイルが正常にアップロードされました'
      })
    )
  })
]

const server = setupServer(...handlers)

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))

// Reset handlers after each test
afterEach(() => server.resetHandlers())

// Close server after all tests
afterAll(() => server.close())

// Global test setup
beforeAll(() => {
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => {},
    }),
  })

  // Mock ResizeObserver
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }

  // Mock IntersectionObserver
  global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    observe() {}
    unobserve() {}
    disconnect() {}
  }
})