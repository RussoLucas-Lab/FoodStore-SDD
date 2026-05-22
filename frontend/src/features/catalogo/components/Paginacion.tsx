interface PaginacionProps {
  page: number
  size: number
  total: number
  pages: number
  onPageChange: (page: number) => void
}

export function Paginacion({
  page,
  size,
  total,
  pages,
  onPageChange,
}: PaginacionProps) {
  if (total <= size) return null

  const pageNumbers: number[] = []
  const maxVisible = 5
  let start = Math.max(1, page - Math.floor(maxVisible / 2))
  const end = Math.min(pages, start + maxVisible - 1)
  start = Math.max(1, end - maxVisible + 1)

  for (let i = start; i <= end; i++) {
    pageNumbers.push(i)
  }

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="
          px-3 py-1.5 text-sm rounded-md border border-border-color
          text-text-secondary disabled:opacity-40 disabled:cursor-not-allowed
          hover:bg-surface transition-colors
        "
      >
        Anterior
      </button>

      {start > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-1.5 text-sm rounded-md border border-border-color text-text-secondary hover:bg-surface transition-colors"
          >
            1
          </button>
          {start > 2 && <span className="text-text-secondary text-sm">…</span>}
        </>
      )}

      {pageNumbers.map((n) => (
        <button
          key={n}
          onClick={() => onPageChange(n)}
          className={`
            px-3 py-1.5 text-sm rounded-md border transition-colors
            ${
              n === page
                ? 'bg-blue text-white border-blue font-medium'
                : 'border-border-color text-text-secondary hover:bg-surface'
            }
          `}
        >
          {n}
        </button>
      ))}

      {end < pages && (
        <>
          {end < pages - 1 && (
            <span className="text-text-secondary text-sm">…</span>
          )}
          <button
            onClick={() => onPageChange(pages)}
            className="px-3 py-1.5 text-sm rounded-md border border-border-color text-text-secondary hover:bg-surface transition-colors"
          >
            {pages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= pages}
        className="
          px-3 py-1.5 text-sm rounded-md border border-border-color
          text-text-secondary disabled:opacity-40 disabled:cursor-not-allowed
          hover:bg-surface transition-colors
        "
      >
        Siguiente
      </button>
    </div>
  )
}
