import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute'
import { useAuthStore } from '@/store/authStore'
import type { TokenResponse, UserPublic } from '@/types/auth'

const tokens: TokenResponse = {
  access_token: 'tok',
  refresh_token: 'ref',
  token_type: 'bearer',
  expires_in: 1800,
}
const adminUser: UserPublic = {
  id: 1,
  email: 'a@a.com',
  nombre: 'Admin',
  apellido: 'A',
  rol: 'ADMIN',
  fecha_alta: '2026-01-01T00:00:00Z',
}
const clientUser: UserPublic = { ...adminUser, rol: 'CLIENT' }

function renderWithRouter(
  element: React.ReactNode,
  initialPath = '/protected',
) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/protected" element={element} />
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    useAuthStore.getState().clearSession()
  })

  it('redirige a /login si no está autenticado', () => {
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected</div>
      </ProtectedRoute>,
    )
    expect(screen.getByText('Login page')).toBeInTheDocument()
  })

  it('muestra contenido si está autenticado sin restricción de rol', () => {
    useAuthStore.getState().setSession(tokens, clientUser)
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected content</div>
      </ProtectedRoute>,
    )
    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })

  it('permite acceso si el usuario tiene el rol requerido', () => {
    useAuthStore.getState().setSession(tokens, adminUser)
    renderWithRouter(
      <ProtectedRoute roles={['ADMIN']}>
        <div>Admin content</div>
      </ProtectedRoute>,
    )
    expect(screen.getByText('Admin content')).toBeInTheDocument()
  })

  it('redirige a / si el usuario no tiene el rol requerido', () => {
    useAuthStore.getState().setSession(tokens, clientUser)
    renderWithRouter(
      <ProtectedRoute roles={['ADMIN']}>
        <div>Admin only</div>
      </ProtectedRoute>,
    )
    expect(screen.getByText('Home page')).toBeInTheDocument()
  })
})
