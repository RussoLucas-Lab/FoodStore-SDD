import { Skeleton } from '@/components/Skeleton'

interface KpiCardProps {
  title: string
  value: string | number | undefined
  isLoading?: boolean
  prefix?: string
  suffix?: string
}

export function KpiCard({ title, value, isLoading, prefix, suffix }: KpiCardProps) {
  return (
    <div className="bg-white rounded-xl border border-border-color p-6 flex flex-col gap-2">
      <p className="text-sm text-text-secondary">{title}</p>
      {isLoading ? (
        <Skeleton className="h-8 w-32" />
      ) : (
        <p className="text-2xl font-semibold text-text-primary">
          {prefix}
          {value ?? '—'}
          {suffix}
        </p>
      )}
    </div>
  )
}
