import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '../contexts/AuthContext'
import { CompanyProvider } from '../contexts/CompanyContext'
import ChatInterface from '../ChatInterface'

// Mock the API
vi.mock('../api', () => ({
  sendMessage: vi.fn(),
  uploadDocument: vi.fn(),
  getChatHistory: vi.fn()
}))

const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com', 
  name: 'Test User',
  role: 'user' as const,
  company_id: 'test-company'
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>
    <CompanyProvider>
      {children}
    </CompanyProvider>
  </AuthProvider>
)

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('チャットインターフェースが正しく表示される', () => {
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    expect(screen.getByPlaceholderText('メッセージを入力してください...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /送信/i })).toBeInTheDocument()
  })

  it('メッセージ入力と送信が正しく動作する', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /送信/i })

    await user.type(input, 'テストメッセージ')
    expect(input).toHaveValue('テストメッセージ')

    await user.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('テストメッセージ')).toBeInTheDocument()
    })
  })

  it('Enterキーでメッセージ送信ができる', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    
    await user.type(input, 'Enterキーテスト')
    await user.keyboard('{Enter}')

    await waitFor(() => {
      expect(screen.getByText('Enterキーテスト')).toBeInTheDocument()
    })
  })

  it('空のメッセージは送信できない', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const sendButton = screen.getByRole('button', { name: /送信/i })
    
    // 空の状態で送信ボタンをクリック
    await user.click(sendButton)

    // エラーメッセージまたは送信失敗を確認
    expect(sendButton).toBeDisabled()
  })

  it('ファイルアップロード機能が正しく動作する', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    // ファイルアップロードボタンを探す
    const fileInput = screen.getByLabelText(/ファイルアップロード/i) || 
                     screen.getByRole('button', { name: /アップロード/i })

    if (fileInput) {
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      
      await user.upload(fileInput as HTMLInputElement, file)

      await waitFor(() => {
        expect(screen.getByText(/test.pdf/)).toBeInTheDocument()
      })
    }
  })

  it('チャット履歴が正しく表示される', async () => {
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    // モックデータが表示されるまで待機
    await waitFor(() => {
      expect(screen.getByText('テスト質問')).toBeInTheDocument()
      expect(screen.getByText('テスト回答')).toBeInTheDocument()
    })
  })

  it('ボット応答が正しく表示される', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /送信/i })

    await user.type(input, 'こんにちは')
    await user.click(sendButton)

    // ボットの応答を待つ
    await waitFor(() => {
      expect(screen.getByText('こんにちは！テストメッセージの回答です。')).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('エラー状態が正しく処理される', async () => {
    // APIエラーをシミュレート
    const { sendMessage } = await import('../api')
    vi.mocked(sendMessage).mockRejectedValueOnce(new Error('API Error'))

    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /送信/i })

    await user.type(input, 'エラーテスト')
    await user.click(sendButton)

    // エラーメッセージの表示を確認
    await waitFor(() => {
      expect(screen.getByText(/エラーが発生しました/)).toBeInTheDocument()
    })
  })

  it('ローディング状態が正しく表示される', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /送信/i })

    await user.type(input, 'ローディングテスト')
    await user.click(sendButton)

    // ローディングインジケーターの確認
    expect(screen.getByRole('progressbar') || screen.getByText(/送信中/)).toBeInTheDocument()
  })

  it('ソース引用が正しく表示される', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <ChatInterface />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('メッセージを入力してください...')
    const sendButton = screen.getByRole('button', { name: /送信/i })

    await user.type(input, 'ソーステスト')
    await user.click(sendButton)

    // ソース引用の表示を確認
    await waitFor(() => {
      expect(screen.getByText('test-document.pdf')).toBeInTheDocument()
    })
  })
})