"""BaseRepository genérico con operaciones CRUD estándar."""

from typing import Generic, TypeVar, Type, Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Session, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    """Repositorio base con operaciones CRUD reutilizables.

    Hereda por todos los repositorios de módulo. Recibe la sesión del UoW.
    Sin lógica de negocio — solo queries a BD.
    """

    def __init__(self, session: Session, model: Type[T]) -> None:
        self.session = session
        self.model = model

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Retorna la entidad por ID, o None si no existe."""
        return self.session.get(self.model, entity_id)

    def list_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retorna listado paginado de entidades activas (sin deleted_at)."""
        statement = select(self.model).offset(skip).limit(limit)
        # Filtrar soft delete si el modelo tiene deleted_at
        if hasattr(self.model, "deleted_at"):
            statement = statement.where(
                getattr(self.model, "deleted_at") == None  # noqa: E711
            )
        return list(self.session.exec(statement).all())

    def count(self) -> int:
        """Retorna el conteo total de entidades activas."""
        from sqlalchemy import func, select as sa_select
        stmt = sa_select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(
                getattr(self.model, "deleted_at") == None  # noqa: E711
            )
        result = self.session.exec(stmt)  # type: ignore[arg-type]
        return result.one()

    def create(self, entity: T) -> T:
        """Agrega la entidad a la sesión, hace flush y refresh. Retorna con ID asignado."""
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Persiste cambios sobre una entidad ya tracked por la sesión."""
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    def soft_delete(self, entity: T) -> T:
        """Marca la entidad como eliminada asignando deleted_at a la fecha/hora actual."""
        if not hasattr(entity, "deleted_at"):
            raise AttributeError(
                f"El modelo {type(entity).__name__} no tiene campo deleted_at"
            )
        entity.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        self.session.add(entity)
        self.session.flush()
        return entity

    def hard_delete(self, entity: T) -> None:
        """Elimina físicamente la entidad de la BD. Usar solo en tablas técnicas."""
        self.session.delete(entity)
        self.session.flush()
