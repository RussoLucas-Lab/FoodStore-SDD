import { useForm } from '@tanstack/react-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useUiStore } from '@/store/uiStore'
import { useChangePassword } from '../hooks/usePerfil'

export function CambiarPasswordForm() {
  const changePasswordMutation = useChangePassword()
  const addToast = useUiStore((s) => s.addToast)

  const form = useForm({
    defaultValues: {
      password_actual: '',
      password_nuevo: '',
      password_nuevo_confirmar: '',
    },
    onSubmit: async ({ value }) => {
      try {
        await changePasswordMutation.mutateAsync(value)
        addToast('Contraseña actualizada correctamente.', 'success')
        form.reset()
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } } }
        const message =
          error.response?.data?.detail ?? 'No se pudo cambiar la contraseña.'
        addToast(message, 'error')
      }
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        void form.handleSubmit()
      }}
      className="flex flex-col gap-4"
    >
      <form.Field
        name="password_actual"
        validators={{
          onChange: ({ value }) =>
            !value ? 'Ingresá tu contraseña actual' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Contraseña actual"
            type="password"
            autoComplete="current-password"
            value={field.state.value}
            onChange={(e) => field.handleChange(e.target.value)}
            onBlur={field.handleBlur}
            error={
              field.state.meta.isTouched
                ? field.state.meta.errors[0]
                : undefined
            }
          />
        )}
      </form.Field>

      <form.Field
        name="password_nuevo"
        validators={{
          onChange: ({ value }) =>
            value.length < 8 ? 'Mínimo 8 caracteres' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Nueva contraseña"
            type="password"
            autoComplete="new-password"
            value={field.state.value}
            onChange={(e) => field.handleChange(e.target.value)}
            onBlur={field.handleBlur}
            error={
              field.state.meta.isTouched
                ? field.state.meta.errors[0]
                : undefined
            }
          />
        )}
      </form.Field>

      <form.Field
        name="password_nuevo_confirmar"
        validators={{
          onChangeListenTo: ['password_nuevo'],
          onChange: ({ value, fieldApi }) => {
            const nuevo = fieldApi.form.getFieldValue('password_nuevo')
            if (!value) return 'Confirmá la nueva contraseña'
            if (value !== nuevo) return 'Las contraseñas no coinciden'
            return undefined
          },
        }}
      >
        {(field) => (
          <Input
            label="Confirmar nueva contraseña"
            type="password"
            autoComplete="new-password"
            value={field.state.value}
            onChange={(e) => field.handleChange(e.target.value)}
            onBlur={field.handleBlur}
            error={
              field.state.meta.isTouched
                ? field.state.meta.errors[0]
                : undefined
            }
          />
        )}
      </form.Field>

      <Button
        type="submit"
        loading={changePasswordMutation.isPending}
        disabled={changePasswordMutation.isPending}
        className="self-start"
      >
        Cambiar contraseña
      </Button>
    </form>
  )
}
