import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { RegisterForm } from '@/features/auth/components/RegisterForm'
import { useAuthStore } from '@/store/authStore'

vi.mock('@/api/endpoints/auth', () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    getMe: vi.fn(),
  },
}))

function renderRegisterForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <RegisterForm />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('RegisterForm', () => {
  beforeEach(() => {
    useAuthStore.getState().clearSession()
    vi.clearAllMocks()
  })

  it('renderiza todos los campos', () => {
    renderRegisterForm()
    expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/apellido/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^contraseña/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirmar/i)).toBeInTheDocument()
  })

  it('muestra error cuando las contraseñas no coinciden', async () => {
    renderRegisterForm()
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'a@b.com' },
    })
    fireEvent.change(screen.getByLabelText(/^contraseña/i), {
      target: { value: 'Segura123!' },
    })
    fireEvent.change(screen.getByLabelText(/confirmar/i), {
      target: { value: 'Diferente!' },
    })
    fireEvent.change(screen.getByLabelText(/^nombre/i), {
      target: { value: 'Juan' },
    })
    fireEvent.change(screen.getByLabelText(/apellido/i), {
      target: { value: 'Pérez' },
    })
    fireEvent.click(screen.getByRole('button', { name: /crear/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/contraseñas no coinciden/i),
      ).toBeInTheDocument()
    })
  })

  it('mapea el error 409 de email al campo email', async () => {
    const { authApi } = await import('@/api/endpoints/auth')
    vi.mocked(authApi.register).mockRejectedValueOnce({
      response: {
        status: 409,
        data: { code: 'EMAIL_ALREADY_EXISTS', field: 'email', detail: 'El email ya está registrado.' },
      },
    })

    renderRegisterForm()
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'duplicado@test.com' },
    })
    fireEvent.change(screen.getByLabelText(/^contraseña/i), {
      target: { value: 'Segura123!' },
    })
    fireEvent.change(screen.getByLabelText(/confirmar/i), {
      target: { value: 'Segura123!' },
    })
    fireEvent.change(screen.getByLabelText(/^nombre/i), {
      target: { value: 'Juan' },
    })
    fireEvent.change(screen.getByLabelText(/apellido/i), {
      target: { value: 'Pérez' },
    })
    fireEvent.click(screen.getByRole('button', { name: /crear/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/email ya está registrado/i),
      ).toBeInTheDocument()
    })
  })
})
