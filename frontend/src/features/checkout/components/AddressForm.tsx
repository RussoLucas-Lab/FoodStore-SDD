/**
 * AddressForm — formulario inline reutilizable para alta y edición de direcciones.
 *
 * Usa TanStack Form con validación inline de campos requeridos.
 * Recibe initialValues? (modo edición) y onSubmit.
 */

import { useForm } from '@tanstack/react-form'
import type { DireccionCreate, DireccionUpdate } from '@/types/direcciones'

type FormValues = {
  calle: string
  numero: string
  piso: string
  depto: string
  ciudad: string
  provincia: string
  codigo_postal: string
  referencia: string
}

interface AddressFormProps {
  initialValues?: Partial<FormValues>
  onSubmit: (data: DireccionCreate | DireccionUpdate) => void
  onCancel: () => void
  isPending?: boolean
}

export function AddressForm({ initialValues, onSubmit, onCancel, isPending }: AddressFormProps) {
  const form = useForm<FormValues>({
    defaultValues: {
      calle: initialValues?.calle ?? '',
      numero: initialValues?.numero ?? '',
      piso: initialValues?.piso ?? '',
      depto: initialValues?.depto ?? '',
      ciudad: initialValues?.ciudad ?? '',
      provincia: initialValues?.provincia ?? '',
      codigo_postal: initialValues?.codigo_postal ?? '',
      referencia: initialValues?.referencia ?? '',
    },
    onSubmit: async ({ value }) => {
      const payload: DireccionCreate = {
        calle: value.calle.trim(),
        numero: value.numero.trim(),
        ciudad: value.ciudad.trim(),
        provincia: value.provincia.trim(),
        codigo_postal: value.codigo_postal.trim(),
        piso: value.piso.trim() || undefined,
        depto: value.depto.trim() || undefined,
        referencia: value.referencia.trim() || undefined,
      }
      onSubmit(payload)
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        void form.handleSubmit()
      }}
      className="flex flex-col gap-3 p-4 bg-surface border border-border-color rounded-md"
    >
      <p className="text-text-primary font-medium text-sm">
        {initialValues ? 'Editar dirección' : 'Nueva dirección'}
      </p>

      {/* Calle */}
      <form.Field
        name="calle"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'La calle es requerida.' : undefined) }}
      >
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Calle *
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="Av. Corrientes"
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-xs text-error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      {/* Número */}
      <form.Field
        name="numero"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'El número es requerido.' : undefined) }}
      >
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Número *
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="1234"
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-xs text-error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      {/* Piso / Depto — en fila */}
      <div className="flex gap-3">
        <form.Field name="piso">
          {(field) => (
            <div className="flex flex-col gap-1 flex-1">
              <label className="text-xs text-text-secondary" htmlFor={field.name}>
                Piso
              </label>
              <input
                id={field.name}
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                placeholder="3"
                className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
              />
            </div>
          )}
        </form.Field>
        <form.Field name="depto">
          {(field) => (
            <div className="flex flex-col gap-1 flex-1">
              <label className="text-xs text-text-secondary" htmlFor={field.name}>
                Depto
              </label>
              <input
                id={field.name}
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                placeholder="B"
                className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
              />
            </div>
          )}
        </form.Field>
      </div>

      {/* Ciudad */}
      <form.Field
        name="ciudad"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'La ciudad es requerida.' : undefined) }}
      >
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Ciudad *
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="Buenos Aires"
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-xs text-error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      {/* Provincia */}
      <form.Field
        name="provincia"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'La provincia es requerida.' : undefined) }}
      >
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Provincia *
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="CABA"
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-xs text-error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      {/* Código Postal */}
      <form.Field
        name="codigo_postal"
        validators={{ onChange: ({ value }) => (!value.trim() ? 'El código postal es requerido.' : undefined) }}
      >
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Código postal *
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="C1414"
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
            {field.state.meta.errors.length > 0 && (
              <span className="text-xs text-error">{field.state.meta.errors[0]}</span>
            )}
          </div>
        )}
      </form.Field>

      {/* Referencia */}
      <form.Field name="referencia">
        {(field) => (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-secondary" htmlFor={field.name}>
              Referencia
            </label>
            <input
              id={field.name}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              placeholder="Portero automático, timbre nombre..."
              className="border border-border-color rounded px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-blue"
            />
          </div>
        )}
      </form.Field>

      {/* Acciones */}
      <div className="flex gap-3 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 py-2 rounded border border-border-color text-text-secondary text-sm font-medium hover:bg-surface-alt transition-colors"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="flex-1 py-2 rounded bg-blue text-white text-sm font-medium hover:bg-blue-dark disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}
