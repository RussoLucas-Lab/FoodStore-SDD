"""Servicio de lógica de negocio para Ingrediente."""

import math
from typing import Optional

from fastapi import HTTPException, status

from app.modules.ingredientes.model import Ingrediente
from app.modules.ingredientes.schemas import (
    IngredienteCreate,
    IngredienteRead,
    IngredienteUpdate,
    PaginatedIngredientes,
)


class IngredienteService:
    """Lógica de negocio stateless para Ingrediente. Nunca llama session.commit()."""

    def list_all(
        self,
        uow,
        page: int = 1,
        size: int = 20,
        es_alergeno: Optional[bool] = None,
    ) -> PaginatedIngredientes:
        """Lista ingredientes con paginación y filtro opcional por es_alergeno."""
        items, total = uow.ingredientes.list_paginated(page, size, es_alergeno)
        pages = math.ceil(total / size) if size > 0 else 0
        return PaginatedIngredientes(
            items=[IngredienteRead.model_validate(i) for i in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def get_by_id(self, uow, ingrediente_id: int) -> IngredienteRead:
        """Retorna un ingrediente por ID. 404 si no existe o está eliminado."""
        ing = uow.ingredientes.get_by_id(ingrediente_id)
        if ing is None or ing.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Ingrediente con id {ingrediente_id} no encontrado.",
                    "code": "INGREDIENTE_NOT_FOUND",
                },
            )
        return IngredienteRead.model_validate(ing)

    def create(self, uow, body: IngredienteCreate) -> IngredienteRead:
        """Crea un nuevo ingrediente. 409 si el nombre ya existe."""
        existing = uow.ingredientes.get_by_nombre(body.nombre)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "detail": f"Ya existe un ingrediente con el nombre '{body.nombre}'.",
                    "code": "INGREDIENTE_DUPLICATE",
                },
            )

        nuevo = Ingrediente(nombre=body.nombre, es_alergeno=body.es_alergeno)
        created = uow.ingredientes.create(nuevo)
        return IngredienteRead.model_validate(created)

    def update(self, uow, ingrediente_id: int, body: IngredienteUpdate) -> IngredienteRead:
        """Actualiza un ingrediente existente. 404 si no existe."""
        ing = uow.ingredientes.get_by_id(ingrediente_id)
        if ing is None or ing.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Ingrediente con id {ingrediente_id} no encontrado.",
                    "code": "INGREDIENTE_NOT_FOUND",
                },
            )

        if body.nombre is not None:
            ing.nombre = body.nombre
        if body.es_alergeno is not None:
            ing.es_alergeno = body.es_alergeno

        updated = uow.ingredientes.update(ing)
        return IngredienteRead.model_validate(updated)

    def delete(self, uow, ingrediente_id: int) -> None:
        """Elimina (soft delete) un ingrediente. 404 si no existe."""
        ing = uow.ingredientes.get_by_id(ingrediente_id)
        if ing is None or ing.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Ingrediente con id {ingrediente_id} no encontrado.",
                    "code": "INGREDIENTE_NOT_FOUND",
                },
            )

        uow.ingredientes.soft_delete(ing)


ingrediente_service = IngredienteService()
