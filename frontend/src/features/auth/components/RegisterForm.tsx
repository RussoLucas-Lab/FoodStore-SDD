import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from '@tanstack/react-form'
import type { AxiosError } from 'axios'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useRegister } from '@/features/auth/hooks/useRegister'

interface ErrorBody {
  code?: string
  detail?: string
  field?: string
}

export function RegisterForm() {
  const registerMutation = useRegister()
  const navigate = useNavigate()
  const [emailError, setEmailError] = useState<string | null>(null)
  const [globalError, setGlobalError] = useState<string | null>(null)

  const form = useForm({
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      nombre: '',
      apellido: '',
    },
    onSubmit: async ({ value }) => {
      setEmailError(null)
      setGlobalError(null)

      if (value.password !== value.confirmPassword) {
        setGlobalError('Las contraseñas no coinciden.')
        return
      }

      try {
        await registerMutation.mutateAsync({
          email: value.email,
          password: value.password,
          nombre: value.nombre,
          apellido: value.apellido,
        })
        navigate('/')
      } catch (err) {
        const axiosErr = err as AxiosError<ErrorBody>
        const status = axiosErr.response?.status
        const body = axiosErr.response?.data

        if (status === 409 && body?.field === 'email') {
          setEmailError(body?.detail ?? 'El email ya está registrado.')
        } else {
          setGlobalError('Ocurrió un error al crear la cuenta. Intentá de nuevo.')
        }
      }
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        void form.handleSubmit()
      }}
      className="flex flex-col gap-5"
    >
      <div className="grid grid-cols-2 gap-4">
        <form.Field
          name="nombre"
          validators={{
            onChange: ({ value }) =>
              !value.trim() ? 'Requerido' : undefined,
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
              !value.trim() ? 'Requerido' : undefined,
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
      </div>

      <form.Field
        name="email"
        validators={{
          onChange: ({ value }) =>
            !value.includes('@') ? 'Ingresá un email válido' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            value={field.state.value}
            onChange={(e) => {
              field.handleChange(e.target.value)
              setEmailError(null)
            }}
            onBlur={field.handleBlur}
            error={
              emailError ??
              (field.state.meta.isTouched
                ? field.state.meta.errors[0]
                : undefined)
            }
          />
        )}
      </form.Field>

      <form.Field
        name="password"
        validators={{
          onChange: ({ value }) =>
            value.length < 8 ? 'Mínimo 8 caracteres' : undefined,
        }}
      >
        {(field) => (
          <Input
            label="Contraseña"
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

      <form.Field name="confirmPassword">
        {(field) => (
          <Input
            label="Confirmar contraseña"
            type="password"
            autoComplete="new-password"
            value={field.state.value}
            onChange={(e) => field.handleChange(e.target.value)}
            onBlur={field.handleBlur}
          />
        )}
      </form.Field>

      {globalError && (
        <p className="text-sm text-error text-center" role="alert">
          {globalError}
        </p>
      )}

      <Button
        type="submit"
        loading={registerMutation.isPending}
        disabled={registerMutation.isPending}
      >
        Crear cuenta
      </Button>
    </form>
  )
}
