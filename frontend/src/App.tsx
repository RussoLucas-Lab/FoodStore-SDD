/**
 * App — rutas de Food Store con layouts y ProtectedRoute.
 *
 * Rutas públicas: /, /login, /register → AppLayout
 * Rutas cliente:  /pedidos, /checkout  → AppLayout + ProtectedRoute (sin rol requerido)
 * Rutas admin:    /admin/*             → ProtectedRoute(ADMIN|STOCK|PEDIDOS) + AdminLayout
 * Catch-all:      *                    → NotFoundPage
 */

import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layouts/AppLayout'
import { AdminLayout } from '@/components/layouts/AdminLayout'
import { ProtectedRoute } from '@/features/auth/components/ProtectedRoute'
import { useCurrentUser } from '@/features/auth/hooks/useCurrentUser'
import { useAuthStore } from '@/store/authStore'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import CatalogoPage from './pages/CatalogoPage'
import PedidosPage from './pages/PedidosPage'
import PedidoDetailPage from './pages/PedidoDetailPage'
import CheckoutPage from './pages/CheckoutPage'
import PedidoConfirmadoPage from './pages/PedidoConfirmadoPage'
import PagoExitosoPage from './pages/PagoExitosoPage'
import PagoRechazadoPage from './pages/PagoRechazadoPage'
import PerfilPage from './pages/PerfilPage'
import AdminCategoriasPage from './pages/AdminCategoriasPage'
import AdminIngredientesPage from './pages/AdminIngredientesPage'
import GestionPedidosPage from './pages/GestionPedidosPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import AdminUsuariosPage from './pages/AdminUsuariosPage'
import AdminStockPage from './pages/AdminStockPage'
import AdminConfiguracionPage from './pages/AdminConfiguracionPage'
import NotFoundPage from './pages/NotFoundPage'

function AppRoutes() {
  // Esperar a que Zustand termine de hidratar desde localStorage
  // (persist usa toThenable que puede ser asíncrono)
  const [hydrated, setHydrated] = useState(
    useAuthStore.persist.hasHydrated()
  )

  useEffect(() => {
    if (!hydrated) {
      const unsub = useAuthStore.persist.onFinishHydration(() => {
        setHydrated(true)
      })
      return unsub
    }
  }, [hydrated])

  // Bootstrap: si hay accessToken persistido, reconstruye usuario via /me
  useCurrentUser()

  return (
    <Routes>
      {/* Rutas públicas */}
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/catalogo" element={<CatalogoPage />} />

        {/* Rutas protegidas (cualquier usuario autenticado) */}
        <Route
          path="/pedidos"
          element={
            <ProtectedRoute roles={['CLIENT']}>
              <PedidosPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pedidos/:id"
          element={
            <ProtectedRoute roles={['CLIENT']}>
              <PedidoDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout"
          element={
            <ProtectedRoute>
              <CheckoutPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout/confirmado"
          element={
            <ProtectedRoute>
              <PedidoConfirmadoPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout/pago-exitoso"
          element={
            <ProtectedRoute>
              <PagoExitosoPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/checkout/pago-rechazado"
          element={
            <ProtectedRoute>
              <PagoRechazadoPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/perfil"
          element={
            <ProtectedRoute>
              <PerfilPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Rutas admin */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute roles={['ADMIN', 'STOCK', 'PEDIDOS']}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminDashboardPage />} />
        <Route path="categorias" element={<AdminCategoriasPage />} />
        <Route path="ingredientes" element={<AdminIngredientesPage />} />
        <Route
          path="pedidos"
          element={
            <ProtectedRoute roles={['ADMIN', 'PEDIDOS']}>
              <GestionPedidosPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="usuarios"
          element={
            <ProtectedRoute roles={['ADMIN']}>
              <AdminUsuariosPage />
            </ProtectedRoute>
          }
        />
        <Route path="stock" element={<AdminStockPage />} />
        <Route
          path="configuracion"
          element={
            <ProtectedRoute roles={['ADMIN']}>
              <AdminConfiguracionPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<AdminDashboardPage />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return <AppRoutes />
}
