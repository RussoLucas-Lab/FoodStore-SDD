"""Servicio de lógica de negocio para Direccion.

Nunca llama session.commit() — las transacciones las gestiona el UoW.
"""

from typing import List

from fastapi import HTTPException, status

from app.modules.direcciones.model import Direccion
from app.modules.direcciones.schemas import (
    DireccionCreate,
    DireccionRead,
    DireccionSetPrincipalResponse,
    DireccionUpdate,
)


class DireccionService:
    """Lógica de negocio stateless para Direccion."""

    def listar_propias(self, uow, usuario_id: int) -> List[DireccionRead]:
        """Retorna las direcciones activas del usuario autenticado (principal primero)."""
        direcciones = uow.direcciones.list_by_usuario(usuario_id)
        return [DireccionRead.model_validate(d) for d in direcciones]

    def crear(self, uow, usuario_id: int, body: DireccionCreate) -> DireccionRead:
        """Crea una nueva dirección. RN-DI01: primera dirección = principal automática."""
        count = uow.direcciones.count_activas_by_usuario(usuario_id)
        es_principal = True if count == 0 else body.es_principal

        nueva = Direccion(
            usuario_id=usuario_id,
            calle=body.calle,
            numero=body.numero,
            piso=body.piso,
            depto=body.depto,
            ciudad=body.ciudad,
            provincia=body.provincia,
            codigo_postal=body.codigo_postal,
            referencia=body.referencia,
            es_principal=es_principal,
        )
        created = uow.direcciones.create(nueva)
        return DireccionRead.model_validate(created)

    def actualizar(self, uow, usuario_id: int, direccion_id: int, body: DireccionUpdate) -> DireccionRead:
        """Actualiza los campos editables. Ignora es_principal del body (usar PATCH /principal)."""
        direccion = uow.direcciones.get_by_id_and_usuario(direccion_id, usuario_id)
        if direccion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Dirección no encontrada.", "code": "DIRECCION_NOT_FOUND"},
            )

        if body.calle is not None:
            direccion.calle = body.calle
        if body.numero is not None:
            direccion.numero = body.numero
        if body.piso is not None:
            direccion.piso = body.piso
        if body.depto is not None:
            direccion.depto = body.depto
        if body.ciudad is not None:
            direccion.ciudad = body.ciudad
        if body.provincia is not None:
            direccion.provincia = body.provincia
        if body.codigo_postal is not None:
            direccion.codigo_postal = body.codigo_postal
        if body.referencia is not None:
            direccion.referencia = body.referencia

        updated = uow.direcciones.update(direccion)
        return DireccionRead.model_validate(updated)

    def set_principal(self, uow, usuario_id: int, direccion_id: int) -> DireccionSetPrincipalResponse:
        """RN-DI02: Cambia la dirección principal del usuario de forma atómica.

        Desmarca la actual principal y marca la nueva. Idempotente si ya es principal.
        """
        nueva_principal = uow.direcciones.get_by_id_and_usuario(direccion_id, usuario_id)
        if nueva_principal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Dirección no encontrada.", "code": "DIRECCION_NOT_FOUND"},
            )

        # Idempotente: si ya es principal, no hay nada que hacer
        if not nueva_principal.es_principal:
            # Desmarcar la actual principal
            anterior = uow.direcciones.get_principal_by_usuario(usuario_id)
            if anterior is not None and anterior.id != direccion_id:
                anterior.es_principal = False
                uow.direcciones.update(anterior)

            # Marcar la nueva
            nueva_principal.es_principal = True
            uow.direcciones.update(nueva_principal)

        return DireccionSetPrincipalResponse(
            message="Dirección principal actualizada.",
            direccion=DireccionRead.model_validate(nueva_principal),
        )

    def eliminar(self, uow, usuario_id: int, direccion_id: int) -> None:
        """Soft delete de una dirección. Guard: no se puede borrar la principal si hay otras."""
        direccion = uow.direcciones.get_by_id_and_usuario(direccion_id, usuario_id)
        if direccion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Dirección no encontrada.", "code": "DIRECCION_NOT_FOUND"},
            )

        if direccion.es_principal:
            count = uow.direcciones.count_activas_by_usuario(usuario_id)
            if count > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "Promocioná otra dirección como principal antes de eliminar esta.",
                        "code": "PRINCIPAL_CANNOT_DELETE",
                    },
                )

        uow.direcciones.soft_delete(direccion)


direccion_service = DireccionService()
