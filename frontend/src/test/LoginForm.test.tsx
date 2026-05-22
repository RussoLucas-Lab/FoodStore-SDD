import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { useAuthStore } from '@/store/authStore'

vi.mock('@/api/endpoints/auth', () => ({
  authApi: {
    login: vi.fn(),
    getMe: vi.fn(),
  },
}))

function renderLoginForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <LoginForm />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('LoginForm', () => {
  beforeEach(() => {
    useAuthStore.getState().clearSession()
    vi.clearAllMocks()
  })

  it('renderiza los campos de email y contraseña', () => {
    renderLoginForm()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
  })

  it('muestra error de validación si el email es inválido', async () => {
    renderLoginForm()
    const emailInput = screen.getByLabelText(/email/i)
    fireEvent.change(emailInput, { target: { value: 'noemail' } })
    fireEvent.blur(emailInput)
    await waitFor(() => {
      expect(screen.getByText(/email válido/i)).toBeInTheDocument()
    })
  })

  it('muestra error de validación si la contraseña es corta', async () => {
    renderLoginForm()
    const passInput = screen.getByLabelText(/contraseña/i)
    fireEvent.change(passInput, { target: { value: '123' } })
    fireEvent.blur(passInput)
    await waitFor(() => {
      expect(screen.getByText(/mínimo 8/i)).toBeInTheDocument()
    })
  })

  it('muestra mensaje genérico ante error 401', async () => {
    const { authApi } = await import('@/api/endpoints/auth')
    vi.mocked(authApi.login).mockRejectedValueOnce({
      response: { status: 401, data: { code: 'INVALID_CREDENTIALS' } },
    })

    renderLoginForm()
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'a@b.com' },
    })
    fireEvent.change(screen.getByLabelText(/contraseña/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /iniciar/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/email o contraseña incorrectos/i),
      ).toBeInTheDocument()
    })
  })
})
