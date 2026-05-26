"""Máquina de estados de pedidos (FSM).

Define las transiciones permitidas y los roles que pueden ejecutarlas.
La transición PENDIENTE → CONFIRMADO es exclusivamente automática (vía webhook).
"""

from typing import List


# Mapa de transiciones:
# { estado_desde: { estado_hasta: [roles_permitidos] } }
# Lista vacía especial: ["_SISTEMA"] indica que solo el sistema puede ejecutarla.
TRANSITION_MAP: dict[str, dict[str, List[str]]] = {
    "PENDIENTE": {
        "CONFIRMADO": ["_SISTEMA", "ADMIN", "PEDIDOS"],  # webhook (MP) o confirmación manual (EFECTIVO/TRANSFERENCIA)
        "CANCELADO": ["CLIENT", "ADMIN", "PEDIDOS"],
    },
    "CONFIRMADO": {
        "EN_PREP": ["ADMIN", "PEDIDOS"],
        "CANCELADO": ["ADMIN", "PEDIDOS"],
    },
    "EN_PREP": {
        "EN_CAMINO": ["ADMIN", "PEDIDOS"],
        "CANCELADO": ["ADMIN"],           # Solo ADMIN puede cancelar desde EN_PREP
    },
    "EN_CAMINO": {
        "ENTREGADO": ["ADMIN", "PEDIDOS"],
    },
    # ENTREGADO y CANCELADO son terminales — sin transiciones salientes
    "ENTREGADO": {},
    "CANCELADO": {},
}


class OrderStateMachine:
    """Encapsula la lógica de transiciones de estado de un pedido.

    Proporciona métodos para validar transiciones y verificar efectos de borde.
    Testeable de forma aislada, importada por PedidoService.
    """

    def is_allowed(
        self,
        estado_actual: str,
        nuevo_estado: str,
        roles: List[str],
    ) -> bool:
        """Verifica si la transición es permitida para los roles dados.

        PENDIENTE → CONFIRMADO siempre retorna False para roles humanos
        (debe usarse confirmar_pedido() directamente).

        Args:
            estado_actual: Código del estado actual del pedido.
            nuevo_estado: Código del estado destino.
            roles: Lista de roles del usuario que intenta la transición.

        Returns:
            True si la transición está permitida; False en caso contrario.
        """
        transitions = TRANSITION_MAP.get(estado_actual, {})
        allowed_roles = transitions.get(nuevo_estado)

        if allowed_roles is None:
            return False

        # Excluir _SISTEMA — solo aplica a transiciones automáticas (webhook)
        human_roles = [r for r in allowed_roles if r != "_SISTEMA"]

        for role in roles:
            if role in human_roles:
                return True

        return False

    def is_allowed_for_system(self, estado_actual: str, nuevo_estado: str) -> bool:
        """Verifica si la transición es permitida para el sistema (webhook).

        Solo PENDIENTE → CONFIRMADO está marcada como _SISTEMA.
        """
        transitions = TRANSITION_MAP.get(estado_actual, {})
        allowed_roles = transitions.get(nuevo_estado)

        if allowed_roles is None:
            return False

        return "_SISTEMA" in allowed_roles

    def requiere_motivo(self, nuevo_estado: str) -> bool:
        """Retorna True si la transición al nuevo estado requiere motivo.

        El motivo es obligatorio cuando nuevo_estado == 'CANCELADO' (RN-FS09/RN-FS10).
        """
        return nuevo_estado == "CANCELADO"

    def is_terminal(self, estado: str) -> bool:
        """Retorna True si el estado es terminal (sin transiciones salientes)."""
        return TRANSITION_MAP.get(estado) == {} or estado in ("ENTREGADO", "CANCELADO")

    def get_allowed_transitions(self, estado_actual: str, roles: List[str]) -> List[str]:
        """Retorna la lista de estados destino accesibles para los roles dados."""
        transitions = TRANSITION_MAP.get(estado_actual, {})
        result = []
        for nuevo_estado, allowed_roles in transitions.items():
            if "_SISTEMA" not in allowed_roles:
                for role in roles:
                    if role in allowed_roles:
                        result.append(nuevo_estado)
                        break
        return result


# Instancia singleton
order_fsm = OrderStateMachine()
