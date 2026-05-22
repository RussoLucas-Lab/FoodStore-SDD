import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { ToastContainer } from '@/components/Toast'
import { CartDrawer } from '@/features/carrito/components/CartDrawer'
import { useUiStore } from '@/store/uiStore'

export function AppLayout() {
  const toasts = useUiStore((s) => s.toasts)
  const removeToast = useUiStore((s) => s.removeToast)

  return (
    <div className="min-h-screen flex flex-col bg-surface">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-border-color py-4 text-center text-xs text-text-tertiary">
        © {new Date().getFullYear()} Food Store
      </footer>

      {/* CartDrawer montado una sola vez en el layout raíz */}
      <CartDrawer />

      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  )
}
