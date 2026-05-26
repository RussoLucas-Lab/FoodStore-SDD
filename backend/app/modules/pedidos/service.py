"""Servicios para el módulo de pedidos."""

from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.modules.pedidos.fsm import order_fsm
from app.modules.pedidos.model import DetallePedido, HistorialEstadoPedido, Pedido
from app.modules.pedidos.schemas import (
    CambiarEstadoResponse,
    DetallePedidoRead,
    FormaPagoRead,
    HistorialEstadoRead,
    PedidoCreate,
    PedidoDetailRead,
    PedidoRead,
)
from app.modules.pagos.schemas import PagoRead

if TYPE_CHECKING:
    from app.core.uow import UnitOfWork


class FormaPagoService:
    """Servicio para formas de pago."""

    def list_habilitadas(self, uow: "UnitOfWork") -> List[FormaPagoRead]:
        """Lista las formas de pago con habilitado=True."""
        formas = uow.formas_pago.list_habilitadas()
        return [FormaPagoRead.model_validate(f) for f in formas]


class PedidoService:
    """Servicio de creación atómica de pedidos (RN-PE01)."""

    def crear(
        self,
        uow: "UnitOfWork",
        usuario_id: int,
        body: PedidoCreate,
        idempotency_key: Optional[str] = None,
    ) -> PedidoRead:
        """Crea un pedido completo en una sola transacción UoW.

        Valida: forma_pago, dirección, disponibilidad y stock de cada producto,
        personalización. Toma snapshots de precio/nombre/dirección.
        El UoW es quien gestiona commit/rollback — el service nunca lo hace.
        """
        # Idempotency: si ya existe un pedido del usuario con esta key, devolverlo
        if idempotency_key:
            existing = uow.pedidos.get_by_usuario_idempotency_key(usuario_id, idempotency_key)
            if existing:
                return PedidoRead.model_validate(existing)

        # Validar forma de pago
        forma_pago = uow.formas_pago.get_by_codigo(body.forma_pago_codigo)
        if not forma_pago or not forma_pago.habilitado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "detail": "Forma de pago no encontrada o deshabilitada",
                    "code": "FORMA_PAGO_NOT_FOUND",
                    "field": "forma_pago_codigo",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
            )

        # Validar dirección pertenece al usuario (RN-PE03)
        direccion = uow.direcciones.get_by_id_and_usuario(body.direccion_id, usuario_id)
        if not direccion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Dirección no encontrada",
                    "code": "DIRECCION_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        # Adquirir lock pesimista ordenado por id ascendente (evita deadlocks en PostgreSQL)
        producto_ids = sorted(set(item.producto_id for item in body.items))
        locked_productos = uow.productos.lock_productos(producto_ids)
        producto_map = {p.id: p for p in locked_productos}

        # Validar cada item del carrito
        for item in body.items:
            producto = producto_map.get(item.producto_id)
            if not producto:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": f"Producto {item.producto_id} no encontrado",
                        "code": "PRODUCTO_NOT_FOUND",
                        "field": "producto_id",
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                )
            if not producto.disponible:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "detail": f"Producto {item.producto_id} no disponible",
                        "code": "PRODUCTO_NO_DISPONIBLE",
                        "field": "producto_id",
                        "status": status.HTTP_409_CONFLICT,
                    },
                )
            if producto.stock_cantidad < item.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "detail": f"Stock insuficiente para producto {item.producto_id}",
                        "code": "STOCK_INSUFICIENTE",
                        "field": "producto_id",
                        "status": status.HTTP_409_CONFLICT,
                    },
                )

            # Validar ingredientes de personalización pertenecen al producto
            if item.personalizacion:
                pi_list = uow.productos.get_ingredientes(item.producto_id)
                valid_ing_ids = {pi.ingrediente_id for pi in pi_list}
                for ing_id in item.personalizacion:
                    if ing_id not in valid_ing_ids:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "detail": f"Ingrediente {ing_id} no pertenece al producto {item.producto_id}",
                                "code": "INGREDIENTE_NO_DEL_PRODUCTO",
                                "field": "personalizacion",
                                "status": status.HTTP_400_BAD_REQUEST,
                            },
                        )

        # Snapshot inmutable de la dirección (RN-PE03)
        direccion_snapshot = {
            "id": direccion.id,
            "calle": direccion.calle,
            "numero": direccion.numero,
            "piso": direccion.piso,
            "depto": direccion.depto,
            "ciudad": direccion.ciudad,
            "provincia": direccion.provincia,
            "codigo_postal": direccion.codigo_postal,
            "referencia": direccion.referencia,
            "es_principal": direccion.es_principal,
        }

        # Calcular total con precio_snapshot (RN-PE08; costo_envio=0 en Sprint 5)
        costo_envio = Decimal("0")
        total = costo_envio
        for item in body.items:
            precio = Decimal(str(producto_map[item.producto_id].precio_base))
            total += precio * item.cantidad

        # Crear Pedido en estado PENDIENTE
        nuevo_pedido = Pedido(
            usuario_id=usuario_id,
            estado_codigo="PENDIENTE",
            direccion_snapshot=direccion_snapshot,
            total=total,
            costo_envio=costo_envio,
            forma_pago_codigo=body.forma_pago_codigo,
            idempotency_key=idempotency_key,
        )
        nuevo_pedido = uow.pedidos.create(nuevo_pedido)

        # Crear DetallePedido con snapshots de precio y nombre (RN-PE02)
        for item in body.items:
            producto = producto_map[item.producto_id]
            detalle = DetallePedido(
                pedido_id=nuevo_pedido.id,
                producto_id=item.producto_id,
                precio_snapshot=Decimal(str(producto.precio_base)),
                nombre_snapshot=producto.nombre,
                cantidad=item.cantidad,
                personalizacion=item.personalizacion if item.personalizacion else None,
            )
            uow.detalle_pedido.create(detalle)

        # Primer registro de historial — append-only (RN-PE06)
        historial = HistorialEstadoPedido(
            pedido_id=nuevo_pedido.id,
            estado_desde=None,
            estado_hasta="PENDIENTE",
            cambiado_por_id=usuario_id,
        )
        uow.historial_pedido.create(historial)

        return PedidoRead.model_validate(nuevo_pedido)


    def cambiar_estado(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        nuevo_estado: str,
        motivo: Optional[str],
        actor_id: int,
        actor_roles: List[str],
    ) -> CambiarEstadoResponse:
        """Cambia el estado de un pedido respetando la FSM (RN-FS01).

        Valida: pedido existe, transición permitida, motivo obligatorio al cancelar.
        Efectos de borde: restaura stock si CONFIRMADO → CANCELADO.
        Crea registro append-only en HistorialEstadoPedido.
        El UoW gestiona commit/rollback — el service delega al contexto UoW.
        """
        # Validar pedido existe
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None or pedido.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        estado_actual = pedido.estado_codigo

        # Validar transición con FSM
        if not order_fsm.is_allowed(estado_actual, nuevo_estado, actor_roles):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": f"No se puede pasar de {estado_actual} a {nuevo_estado}",
                    "code": "TRANSICION_NO_PERMITIDA",
                    "field": "nuevo_estado",
                    "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                },
            )

        # Validar motivo obligatorio al cancelar (RN-FS09/RN-FS10)
        if order_fsm.requiere_motivo(nuevo_estado):
            if not motivo or not motivo.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "detail": "El motivo es obligatorio al cancelar un pedido",
                        "code": "MOTIVO_REQUERIDO",
                        "field": "motivo",
                        "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    },
                )

        # Efecto de borde: decrementar stock al confirmar manualmente (EFECTIVO/TRANSFERENCIA)
        if estado_actual == "PENDIENTE" and nuevo_estado == "CONFIRMADO":
            detalles = uow.pedidos.get_detalles_by_pedido_id(pedido_id)
            for detalle in detalles:
                try:
                    uow.productos.decrement_stock(detalle.producto_id, detalle.cantidad)
                except ValueError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "detail": str(exc),
                            "code": "STOCK_INSUFICIENTE",
                            "status": status.HTTP_409_CONFLICT,
                        },
                    )

        # Efecto de borde: restaurar stock si CONFIRMADO → CANCELADO (RN-FS05)
        if estado_actual == "CONFIRMADO" and nuevo_estado == "CANCELADO":
            detalles = uow.pedidos.get_detalles_by_pedido_id(pedido_id)
            for detalle in detalles:
                uow.productos.increment_stock(detalle.producto_id, detalle.cantidad)

        # Actualizar estado del pedido
        pedido.estado_codigo = nuevo_estado
        pedido.updated_at = datetime.now(timezone.utc)
        if nuevo_estado == "CANCELADO" and motivo:
            pedido.motivo_cancelacion = motivo.strip()
        uow.pedidos.update(pedido)

        # Registro append-only en HistorialEstadoPedido (RN-FS07)
        historial = HistorialEstadoPedido(
            pedido_id=pedido_id,
            estado_desde=estado_actual,
            estado_hasta=nuevo_estado,
            cambiado_por_id=actor_id,
            motivo=motivo.strip() if motivo else None,
        )
        uow.historial_pedido.create(historial)

        return CambiarEstadoResponse(
            id=pedido.id,
            estado_codigo=pedido.estado_codigo,
            estado_anterior=estado_actual,
            total=pedido.total,
            created_at=pedido.created_at,
        )

    def confirmar_pedido(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        actor_id: Optional[int],
    ) -> None:
        """Confirma un pedido exclusivamente vía webhook de pago (RN-FS02, RN-FS03).

        Decrementa stock atómicamente. Hace rollback si stock queda negativo.
        Crea registro en HistorialEstadoPedido.
        Solo puede ser llamado por PagoService.procesar_webhook().
        El UoW gestiona commit/rollback — el service delega al contexto UoW.
        """
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        estado_actual = pedido.estado_codigo

        # Solo confirmar desde PENDIENTE
        if not order_fsm.is_allowed_for_system(estado_actual, "CONFIRMADO"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "detail": f"No se puede confirmar desde estado {estado_actual}",
                    "code": "TRANSICION_NO_PERMITIDA",
                    "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                },
            )

        # Decrementar stock atómicamente (RN-FS03/RN-FS04)
        detalles = uow.pedidos.get_detalles_by_pedido_id(pedido_id)
        for detalle in detalles:
            try:
                uow.productos.decrement_stock(detalle.producto_id, detalle.cantidad)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "detail": str(exc),
                        "code": "STOCK_INSUFICIENTE",
                        "status": status.HTTP_409_CONFLICT,
                    },
                )

        # Actualizar estado
        pedido.estado_codigo = "CONFIRMADO"
        pedido.updated_at = datetime.now(timezone.utc)
        uow.pedidos.update(pedido)

        # Registro append-only en HistorialEstadoPedido (RN-FS07)
        historial = HistorialEstadoPedido(
            pedido_id=pedido_id,
            estado_desde=estado_actual,
            estado_hasta="CONFIRMADO",
            cambiado_por_id=actor_id,
            motivo=None,
        )
        uow.historial_pedido.create(historial)


    # ---------------------------------------------------------------------------
    # Lectura — listar, detalle, historial
    # ---------------------------------------------------------------------------

    def listar(
        self,
        uow: "UnitOfWork",
        actor_id: int,
        actor_roles: List[str],
        estado_codigo: Optional[str],
        page: int,
        size: int,
    ) -> Dict[str, Any]:
        """Lista pedidos con paginación.

        Si actor tiene rol CLIENT, solo ve sus propios pedidos.
        Si actor tiene rol ADMIN o PEDIDOS, ve todos.
        """
        solo_propios = "CLIENT" in actor_roles and not any(
            r in actor_roles for r in ("ADMIN", "PEDIDOS")
        )
        items, total = uow.pedidos.listar_paginado(
            usuario_id=actor_id,
            solo_propios=solo_propios,
            estado_codigo=estado_codigo,
            page=page,
            size=size,
        )
        pages = ceil(total / size) if size > 0 else 0
        return {
            "items": [PedidoRead.model_validate(p) for p in items],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
        }

    def get_detalle(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        actor_id: int,
        actor_roles: List[str],
    ) -> PedidoDetailRead:
        """Retorna el detalle completo de un pedido.

        Para rol CLIENT, verifica que el pedido pertenezca al actor (404 si no).
        """
        pedido = uow.pedidos.get_detalle(pedido_id)
        if pedido is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        # Control de acceso: CLIENT solo puede ver sus propios pedidos
        if "CLIENT" in actor_roles and not any(
            r in actor_roles for r in ("ADMIN", "PEDIDOS")
        ):
            if pedido.usuario_id != actor_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "detail": "Pedido no encontrado",
                        "code": "PEDIDO_NOT_FOUND",
                        "status": status.HTTP_404_NOT_FOUND,
                    },
                )

        # Cargar detalles, historial y pago
        detalles = uow.detalle_pedido.list_by_pedido(pedido_id)
        historial = uow.historial_pedido.list_by_pedido(pedido_id)
        pago = uow.pagos.get_by_pedido_id(pedido_id)

        pago_read: Optional[PagoRead] = None
        if pago is not None:
            pago_read = PagoRead(
                id=pago.id,
                pedido_id=pago.pedido_id,
                estado_pago=pago.estado,
                mp_payment_id=pago.mp_payment_id,
                mp_preference_id=pago.mp_preference_id,
                created_at=pago.created_at,
            )

        return PedidoDetailRead(
            id=pedido.id,
            estado_codigo=pedido.estado_codigo,
            total=pedido.total,
            created_at=pedido.created_at,
            direccion_snapshot=pedido.direccion_snapshot,
            items=[DetallePedidoRead.model_validate(d) for d in detalles],
            historial=[HistorialEstadoRead.model_validate(h) for h in historial],
            pago=pago_read,
        )

    def get_historial(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        actor_id: int,
        actor_roles: List[str],
    ) -> List[HistorialEstadoRead]:
        """Retorna el historial de estados de un pedido en orden cronológico.

        Para rol CLIENT, verifica que el pedido pertenezca al actor (404 si no).
        """
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None or pedido.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        # Control de acceso: CLIENT solo puede ver historial de sus propios pedidos
        if "CLIENT" in actor_roles and not any(
            r in actor_roles for r in ("ADMIN", "PEDIDOS")
        ):
            if pedido.usuario_id != actor_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "detail": "Pedido no encontrado",
                        "code": "PEDIDO_NOT_FOUND",
                        "status": status.HTTP_404_NOT_FOUND,
                    },
                )

        historial = uow.historial_pedido.list_by_pedido(pedido_id)
        return [HistorialEstadoRead.model_validate(h) for h in historial]

    # ---------------------------------------------------------------------------
    # Cancelación propia del cliente
    # ---------------------------------------------------------------------------

    def cancelar_propio(
        self,
        uow: "UnitOfWork",
        pedido_id: int,
        actor_id: int,
        motivo: str,
    ) -> CambiarEstadoResponse:
        """Cancela un pedido propio del cliente (rol CLIENT).

        Verifica que el pedido exista y pertenezca al actor.
        Delega al método cambiar_estado() con nuevo_estado=CANCELADO.
        """
        pedido = uow.pedidos.get_by_id(pedido_id)
        if pedido is None or pedido.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        if pedido.usuario_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": "Pedido no encontrado",
                    "code": "PEDIDO_NOT_FOUND",
                    "status": status.HTTP_404_NOT_FOUND,
                },
            )

        return self.cambiar_estado(
            uow=uow,
            pedido_id=pedido_id,
            nuevo_estado="CANCELADO",
            motivo=motivo,
            actor_id=actor_id,
            actor_roles=["CLIENT"],
        )


pedido_service = PedidoService()
forma_pago_service = FormaPagoService()
