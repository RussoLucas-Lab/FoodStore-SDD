/**
 * uiStore — estado de la interfaz de usuario.
 *
 * NO persiste en localStorage.
 * Gestiona: apertura del carrito, sidebar, y modal de confirmación.
 *
 * Convención: suscribirse por slice.
 * Ejemplo: const cartOpen = useUiStore(s => s.cartOpen)
 */

import { create } from 'zustand'
import type { ToastItem } from '@/components/Toast'

export interface ConfirmModalConfig {
  title: string
  message: string
  onConfirm: () => void
  onCancel?: () => void
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
}

interface UiState {
  cartOpen: boolean
  sidebarOpen: boolean
  confirmModal: ConfirmModalConfig | null
  toasts: ToastItem[]

  toggleCart: () => void
  openCart: () => void
  closeCart: () => void

  toggleSidebar: () => void
  openSidebar: () => void
  closeSidebar: () => void

  openConfirm: (config: ConfirmModalConfig) => void
  closeConfirm: () => void

  addToast: (message: string, variant: ToastItem['variant']) => void
  removeToast: (id: string) => void
}

export const useUiStore = create<UiState>()((set) => ({
  cartOpen: false,
  sidebarOpen: false,
  confirmModal: null,
  toasts: [],

  toggleCart: () => set((s) => ({ cartOpen: !s.cartOpen })),
  openCart: () => set({ cartOpen: true }),
  closeCart: () => set({ cartOpen: false }),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  openSidebar: () => set({ sidebarOpen: true }),
  closeSidebar: () => set({ sidebarOpen: false }),

  openConfirm: (config) => set({ confirmModal: config }),
  closeConfirm: () => set({ confirmModal: null }),

  addToast: (message, variant) =>
    set((s) => ({
      toasts: [
        ...s.toasts,
        { id: crypto.randomUUID(), message, variant },
      ],
    })),

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
