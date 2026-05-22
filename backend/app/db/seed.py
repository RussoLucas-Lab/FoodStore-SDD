"""Seed script — idempotent initial data for Food Store.

Populates: Rol, EstadoPedido, FormaPago, usuario admin, categorías, ingredientes y productos.

Usage:
    python -m app.db.seed
"""

from decimal import Decimal
from sqlmodel import Session, select

from app.db.database import engine
from app.core.security import hash_password
from app.modules.roles.model import Rol, UsuarioRol
from app.modules.usuarios.model import Usuario
from app.modules.pedidos.model import EstadoPedido
from app.modules.pagos.model import FormaPago
from app.modules.categorias.model import Categoria
from app.modules.ingredientes.model import Ingrediente
from app.modules.productos.model import Producto, ProductoCategoria, ProductoIngrediente

# Importar todos los modelos para que SQLAlchemy resuelva las relaciones
import app.modules.auth.model  # noqa: F401
import app.modules.direcciones.model  # noqa: F401


def seed_roles(session: Session) -> None:
    """Crea los cuatro roles base si no existen."""
    roles = [
        Rol(codigo="ADMIN", descripcion="Administrador con acceso total"),
        Rol(codigo="STOCK", descripcion="Gestión de inventario y productos"),
        Rol(codigo="PEDIDOS", descripcion="Gestión de pedidos y entregas"),
        Rol(codigo="CLIENT", descripcion="Cliente registrado"),
    ]
    for rol in roles:
        existing = session.get(Rol, rol.codigo)
        if not existing:
            session.add(rol)
            print(f"  [+] Rol '{rol.codigo}' creado.")
        else:
            print(f"  [=] Rol '{rol.codigo}' ya existe.")


def seed_estados_pedido(session: Session) -> None:
    """Crea los estados del ciclo de vida de un pedido si no existen."""
    estados = [
        EstadoPedido(
            codigo="PENDIENTE",
            descripcion="Pedido creado, esperando confirmación de pago",
            orden=1,
            es_terminal=False,
        ),
        EstadoPedido(
            codigo="CONFIRMADO",
            descripcion="Pago aprobado, pedido confirmado (automático vía webhook)",
            orden=2,
            es_terminal=False,
        ),
        EstadoPedido(
            codigo="EN_PREP",
            descripcion="Pedido en preparación en cocina",
            orden=3,
            es_terminal=False,
        ),
        EstadoPedido(
            codigo="EN_CAMINO",
            descripcion="Pedido en camino al cliente",
            orden=4,
            es_terminal=False,
        ),
        EstadoPedido(
            codigo="ENTREGADO",
            descripcion="Pedido entregado exitosamente",
            orden=5,
            es_terminal=True,
        ),
        EstadoPedido(
            codigo="CANCELADO",
            descripcion="Pedido cancelado",
            orden=6,
            es_terminal=True,
        ),
    ]
    for estado in estados:
        existing = session.get(EstadoPedido, estado.codigo)
        if not existing:
            session.add(estado)
            print(f"  [+] EstadoPedido '{estado.codigo}' creado.")
        else:
            print(f"  [=] EstadoPedido '{estado.codigo}' ya existe.")


def seed_formas_pago(session: Session) -> None:
    """Crea las formas de pago disponibles si no existen."""
    formas = [
        FormaPago(codigo="MERCADOPAGO", descripcion="Pago online via MercadoPago"),
        FormaPago(codigo="EFECTIVO", descripcion="Pago en efectivo al momento de la entrega"),
        FormaPago(codigo="TRANSFERENCIA", descripcion="Transferencia bancaria"),
    ]
    for forma in formas:
        existing = session.get(FormaPago, forma.codigo)
        if not existing:
            session.add(forma)
            print(f"  [+] FormaPago '{forma.codigo}' creada.")
        else:
            print(f"  [=] FormaPago '{forma.codigo}' ya existe.")


def seed_admin_user(session: Session) -> None:
    """Crea el usuario administrador por defecto si no existe y le asigna rol ADMIN."""
    email = "admin@foodstore.com"
    stmt = select(Usuario).where(Usuario.email == email)
    existing = session.exec(stmt).first()

    if not existing:
        admin = Usuario(
            nombre="Admin",
            apellido="FoodStore",
            email=email,
            password_hash=hash_password("Admin1234!"),
            activo=True,
        )
        session.add(admin)
        session.flush()  # Obtiene el ID del admin antes del commit

        # Asignar rol ADMIN via tabla pivot
        usuario_rol = UsuarioRol(
            usuario_id=admin.id,
            rol_codigo="ADMIN",
        )
        session.add(usuario_rol)
        print(f"  [+] Usuario admin '{email}' creado con rol ADMIN.")
    else:
        print(f"  [=] Usuario admin '{email}' ya existe.")


def seed_catalogo(session: Session) -> None:
    """Crea categorías, ingredientes y productos de demo si no existen."""
    # Categorías
    cats_data = [
        ("Hamburguesas", "Nuestras hamburguesas artesanales", None, 1),
        ("Pizzas", "Pizzas al horno de piedra", None, 2),
        ("Bebidas", "Bebidas frías y calientes", None, 3),
        ("Postres", "Dulces para cerrar la comida", None, 4),
        ("Hamburguesas Clásicas", "Con queso y lechuga", None, 1),
        ("Hamburguesas Especiales", "Combinaciones únicas del chef", None, 2),
    ]
    existing_cats = {c.nombre: c for c in session.exec(select(Categoria)).all()}
    cats: dict[str, Categoria] = dict(existing_cats)
    for nombre, desc, parent_nombre, orden in cats_data:
        if nombre not in cats:
            parent_id = cats[parent_nombre].id if parent_nombre and parent_nombre in cats else None
            cat = Categoria(nombre=nombre, descripcion=desc, orden=orden, parent_id=parent_id)
            session.add(cat)
            session.flush()
            cats[nombre] = cat
            print(f"  [+] Categoría '{nombre}' creada.")
        else:
            print(f"  [=] Categoría '{nombre}' ya existe.")

    # Ingredientes
    ings_data = [
        ("Pan brioche", False),
        ("Carne de res 200g", False),
        ("Queso cheddar", False),
        ("Lechuga", False),
        ("Tomate", False),
        ("Cebolla", False),
        ("Salsa especial", False),
        ("Pepino encurtido", False),
        ("Gluten", True),
        ("Lactosa", True),
        ("Mozzarella", False),
        ("Salsa de tomate", False),
        ("Jamón", False),
        ("Pimiento rojo", False),
        ("Aceitunas", False),
        ("Coca-Cola", False),
        ("Agua mineral", False),
        ("Jugo de naranja", False),
        ("Chocolate", False),
        ("Crema", False),
    ]
    existing_ings = {i.nombre: i for i in session.exec(select(Ingrediente)).all()}
    ings: dict[str, Ingrediente] = dict(existing_ings)
    for nombre, es_alergeno in ings_data:
        if nombre not in ings:
            ing = Ingrediente(nombre=nombre, es_alergeno=es_alergeno)
            session.add(ing)
            session.flush()
            ings[nombre] = ing
            print(f"  [+] Ingrediente '{nombre}' creado.")
        else:
            print(f"  [=] Ingrediente '{nombre}' ya existe.")

    # Productos: (nombre, descripcion, precio, stock, imagen_url, categorias, ingredientes_removibles, ingredientes_fijos)
    productos_data = [
        (
            "Hamburguesa Clásica",
            "Pan brioche, carne 200g, queso cheddar, lechuga, tomate",
            Decimal("1500.00"),
            20,
            "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
            ["Hamburguesas", "Hamburguesas Clásicas"],
            ["Lechuga", "Tomate", "Pepino encurtido"],
            ["Pan brioche", "Carne de res 200g", "Queso cheddar", "Salsa especial", "Gluten", "Lactosa"],
        ),
        (
            "Hamburguesa BBQ Especial",
            "Doble carne, cebolla caramelizada, queso doble, salsa BBQ",
            Decimal("2200.00"),
            15,
            "https://images.unsplash.com/photo-1553979459-d2229ba7433b?w=400",
            ["Hamburguesas", "Hamburguesas Especiales"],
            ["Cebolla", "Pepino encurtido"],
            ["Pan brioche", "Carne de res 200g", "Queso cheddar", "Salsa especial", "Gluten", "Lactosa"],
        ),
        (
            "Pizza Margherita",
            "Salsa de tomate, mozzarella fresca y albahaca",
            Decimal("1800.00"),
            10,
            "https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=400",
            ["Pizzas"],
            ["Aceitunas"],
            ["Mozzarella", "Salsa de tomate", "Gluten", "Lactosa"],
        ),
        (
            "Pizza con Jamón y Pimientos",
            "Jamón, pimiento rojo asado y mozzarella",
            Decimal("2000.00"),
            8,
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",
            ["Pizzas"],
            ["Pimiento rojo", "Aceitunas"],
            ["Mozzarella", "Salsa de tomate", "Jamón", "Gluten", "Lactosa"],
        ),
        (
            "Coca-Cola 500ml",
            "Bebida gaseosa refrescante",
            Decimal("600.00"),
            50,
            "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400",
            ["Bebidas"],
            [],
            ["Coca-Cola"],
        ),
        (
            "Agua Mineral 500ml",
            "Agua mineral natural sin gas",
            Decimal("400.00"),
            50,
            "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400",
            ["Bebidas"],
            [],
            ["Agua mineral"],
        ),
        (
            "Jugo de Naranja",
            "Jugo natural de naranja exprimido",
            Decimal("700.00"),
            30,
            "https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400",
            ["Bebidas"],
            [],
            ["Jugo de naranja"],
        ),
        (
            "Brownie de Chocolate",
            "Brownie casero con crema chantilly",
            Decimal("900.00"),
            25,
            "https://images.unsplash.com/photo-1607478900766-efe13248b125?w=400",
            ["Postres"],
            ["Crema"],
            ["Chocolate", "Lactosa", "Gluten"],
        ),
    ]

    existing_prods = {p.nombre: p for p in session.exec(select(Producto)).all()}
    for nombre, desc, precio, stock, imagen_url, cat_nombres, ings_removibles, ings_fijos in productos_data:
        if nombre not in existing_prods:
            prod = Producto(
                nombre=nombre,
                descripcion=desc,
                precio_base=precio,
                stock_cantidad=stock,
                disponible=True,
                imagen_url=imagen_url,
            )
            session.add(prod)
            session.flush()

            for cat_nombre in cat_nombres:
                if cat_nombre in cats:
                    session.add(ProductoCategoria(producto_id=prod.id, categoria_id=cats[cat_nombre].id))

            for ing_nombre in ings_removibles:
                if ing_nombre in ings:
                    session.add(ProductoIngrediente(producto_id=prod.id, ingrediente_id=ings[ing_nombre].id, es_removible=True))

            for ing_nombre in ings_fijos:
                if ing_nombre in ings:
                    session.add(ProductoIngrediente(producto_id=prod.id, ingrediente_id=ings[ing_nombre].id, es_removible=False))

            print(f"  [+] Producto '{nombre}' creado (stock={stock}, precio={precio}).")
        else:
            print(f"  [=] Producto '{nombre}' ya existe.")


def run_seed() -> None:
    """Ejecuta todas las seeds de forma idempotente."""
    print("=== Food Store — Seed ===")
    with Session(engine) as session:
        print("\n[Roles]")
        seed_roles(session)

        print("\n[Estados de Pedido]")
        seed_estados_pedido(session)

        print("\n[Formas de Pago]")
        seed_formas_pago(session)

        print("\n[Usuario Admin]")
        seed_admin_user(session)

        print("\n[Catálogo]")
        seed_catalogo(session)

        session.commit()
        print("\n[OK] Seed completado exitosamente.")


if __name__ == "__main__":
    run_seed()
