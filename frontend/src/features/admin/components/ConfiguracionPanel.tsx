import { useState } from 'react'

interface ConfigEntry {
  key: string
  label: string
  value: string
}

const INITIAL_CONFIG: ConfigEntry[] = [
  { key: 'site_name', label: 'Nombre del sitio', value: 'Food Store' },
  { key: 'contact_email', label: 'Email de contacto', value: 'contacto@foodstore.com' },
  { key: 'currency', label: 'Moneda', value: 'ARS' },
]

export function ConfiguracionPanel() {
  const [config, setConfig] = useState<ConfigEntry[]>(INITIAL_CONFIG)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [savedKey, setSavedKey] = useState<string | null>(null)

  function handleChange(key: string, value: string) {
    setConfig((prev) => prev.map((c) => (c.key === key ? { ...c, value } : c)))
  }

  function handleSave(key: string) {
    setEditingKey(null)
    setSavedKey(key)
    setTimeout(() => setSavedKey(null), 2000)
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-text-primary">Configuración del sistema</h1>
      <p className="text-sm text-text-secondary">
        Estos valores se guardan localmente. La persistencia en base de datos no está implementada en esta versión.
      </p>

      <div className="overflow-x-auto rounded-xl border border-border-color">
        <table className="w-full text-sm">
          <thead className="bg-surface text-text-secondary">
            <tr>
              <th className="px-4 py-3 text-left font-medium w-48">Parámetro</th>
              <th className="px-4 py-3 text-left font-medium">Valor</th>
              <th className="px-4 py-3 text-center font-medium w-32">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-color">
            {config.map((entry) => (
              <tr key={entry.key} className="bg-white">
                <td className="px-4 py-3 font-medium text-text-primary">{entry.label}</td>
                <td className="px-4 py-3">
                  {editingKey === entry.key ? (
                    <input
                      type="text"
                      value={entry.value}
                      onChange={(e) => handleChange(entry.key, e.target.value)}
                      autoFocus
                      className="w-full border border-border-color rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue/30"
                    />
                  ) : (
                    <span className="text-text-primary">{entry.value}</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {editingKey === entry.key ? (
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => handleSave(entry.key)}
                        className="text-xs px-2 py-1 rounded bg-blue text-white"
                      >
                        Guardar
                      </button>
                      <button
                        onClick={() => setEditingKey(null)}
                        className="text-xs px-2 py-1 rounded border border-border-color text-text-secondary"
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : savedKey === entry.key ? (
                    <span className="text-xs text-green-600 font-medium">Guardado</span>
                  ) : (
                    <button
                      onClick={() => setEditingKey(entry.key)}
                      className="text-xs text-blue hover:underline"
                    >
                      Editar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
