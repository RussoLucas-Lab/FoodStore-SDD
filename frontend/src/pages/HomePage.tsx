import { Link } from 'react-router-dom'
import heroBg from '../../assets/FoodStore-main.png'

export default function HomePage() {
  return (
    <div
      className="relative min-h-[calc(100vh-56px)] bg-cover bg-center flex items-center"
      style={{ backgroundImage: `url(${heroBg})` }}
    >
      {/* Overlay oscuro para legibilidad */}
      <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

      {/* Contenido — lado izquierdo */}
      <div className="relative z-10 max-w-grid mx-auto px-6 sm:px-10 lg:px-16 w-full">
        <div className="max-w-md">
          <p className="text-white/60 text-xs font-semibold uppercase tracking-widest mb-4">
            Bienvenido a Food Store
          </p>
          <h1 className="text-5xl sm:text-6xl font-bold text-white leading-tight mb-5">
            El sabor que<br />buscabas,<br />está aquí.
          </h1>
          <p className="text-white/75 text-lg leading-relaxed mb-10">
            Hamburguesas artesanales, pizzas al horno de piedra y mucho más. Pedí ahora y recibí en tu puerta.
          </p>
          <Link
            to="/catalogo"
            className="inline-block bg-white text-text-primary px-8 py-3 rounded-full font-semibold text-sm hover:bg-white/90 transition-colors shadow-modal"
          >
            Ver catálogo →
          </Link>
        </div>
      </div>
    </div>
  )
}
