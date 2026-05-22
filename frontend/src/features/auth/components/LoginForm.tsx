import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import type { AxiosError } from 'axios'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { useLogin } from '@/features/auth/hooks/useLogin'

interface ErrorBody {
  code?: string
  detail?: string
}

export function LoginForm() {
  const loginMutation = useLogin()
  const [globalError, setGlobalError] = useState<string | null>(null)
  const [rateLimitUntil, setRateLimitUntil] = useState<number | null>(null)

  const isRateLimited = rateLimitUntil !== null && Date.now() < rateLimitUntil

  const form = useForm({
    defaultValues: { email: '', password: '' },
    onSubmit: async ({ value }) => {
      setGlobalError(null)
      try {
        await loginMutation.mutateAsync(value)
      } catch (err) {
        const axiosErr = err as AxiosError<ErrorBody>
        const status = axiosErr.response?.status
        const code = axiosErr.response?.data?.code

        if (status === 429 || code === 'RATE_LIMIT_EXCEEDED') {
          setRateLimitUntil(Date.now() + 15 * 60 * 1000)
          setGlobalError(
            'Demasiados intentos. Intente nuevamente en 15 minutos.',
          )
        } else {
          // No diferenciamos email de password (D-4)
          setGlobalError('Email o contraseña incorrectos.')
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

      {globalError && (
        <p className="text-sm text-error text-center" role="alert">
          {globalError}
        </p>
      )}

      <Button
        type="submit"
        loading={loginMutation.isPending}
        disabled={loginMutation.isPending || isRateLimited}
      >
        {isRateLimited ? 'Demasiados intentos' : 'Iniciar sesión'}
      </Button>
    </form>
  )
}
