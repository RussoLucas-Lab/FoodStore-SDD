import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/endpoints/auth'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
})

/**
 * Bootstrap: cuando Zustand termina de hidratar desde localStorage,
 * si hay un accessToken, llamamos /me para reconstruir el objeto usuario.
 * Usamos onFinishHydration porque persist usa toThenable (asíncrono).
 */
function bootstrapSession() {
  const { accessToken, setUsuario, clearSession } = useAuthStore.getState()
  if (!accessToken) return

  authApi.getMe(accessToken)
    .then((res) => {
      setUsuario(res.data)
    })
    .catch(() => {
      // Token expirado o inválido — limpiar sesión
      clearSession()
    })
}

// Si ya hidrató (raro pero posible), bootstrap inmediato
if (useAuthStore.persist.hasHydrated()) {
  bootstrapSession()
} else {
  // Esperamos a que Zustand termine de leer localStorage
  const unsub = useAuthStore.persist.onFinishHydration(() => {
    bootstrapSession()
    unsub()
  })
}

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('No se encontró el elemento root en el DOM')

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
)
