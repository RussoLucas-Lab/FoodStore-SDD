import { useForm } from '@tanstack/react-form'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useUiStore } from '@/store/uiStore'
import { useMe, useUpdateMe } from '../hooks/usePerfil'

export function PerfilForm() {
  const { data: me } = useMe()
  const updateMeMutation = useUpdateMe()
  const addToast = useUiStore((s) => s.addToast)

  const form = useForm({
    defaultValues: {
      nombre: me?.nombre ?? '',
      apellido: me?.apellido ?? '',
    },
    onSubmit: async ({ value }) => {
      try {
        await updateMeMutation.mutateAsync(value)
        addToast('Datos actualizados correctamente.', 'success')
      } catch {
        addToast('No se pudo actualizar el perfil.', 'error')
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
        name="nombre"
        validators={{
          onChange: ({ value }) =>
            !value.trim() ? 'El nombre es obligatorio' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Nombre"
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
        name="apellido"
        validators={{
          onChange: ({ value }) =>
            !value.trim() ? 'El apellido es obligatorio' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Apellido"
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
        loading={updateMeMutation.isPending}
        disabled={updateMeMutation.isPending}
        className="self-start"
      >
        Guardar cambios
      </Button>
    </form>
  )
}
