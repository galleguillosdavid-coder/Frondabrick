"""
IPVN7 In-Flight Transparent Session Rekeying Engine (Dual-Key Grace Window Ratchet)
Implementa la rotación de claves criptográficas y reinicio del contador de secuencia
sin pérdida de paquetes en vuelo ni interrupción de la aplicación.

Garantiza:
1. Derivación determinista de claves de siguiente época mediante HKDF-SHA256.
2. Ventana de gracia concurrente (Dual-Key Grace Window): recepción simultánea de clave nueva y clave previa.
3. Cero pérdida de paquetes (0.0%) ante entrega desordenada de datagramas rezagados en tránsito.
4. Expiración y purga segura de claves antiguas tras agotamiento de la ventana de gracia.
"""

import time
import struct
from typing import Optional, Tuple, Dict, List
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from scripts.ipvn7.core import (
    IPVN7Object,
    IPVN7Container,
    AntiReplayWindow,
)

OBJ_REKEY_ANNOUNCE = 0x07
OBJ_REKEY_ACK = 0x08

RATCHET_SALT = b"IPVN7_RATCHET_SALT_v0"


def derive_next_epoch_keys(current_key: bytes, epoch: int) -> bytes:
    """Deriva la clave de la siguiente época mediante HKDF determinista."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=RATCHET_SALT,
        info=f"epoch_{epoch}".encode("utf-8"),
    )
    return hkdf.derive(current_key)


class RekeyableSessionEndpoint:
    """
    Gestiona una sesión IPVN7 con capacidad de re-claveo transparente en vuelo.
    Mantiene el estado de claves activas y una lista de claves previas en gracia.
    """
    def __init__(self, local_rx_index: int, remote_rx_index: int, send_key: bytes, recv_key: bytes, rekey_threshold: int = 50, grace_period_sec: float = 2.0):
        self.epoch = 1
        self.local_rx_index = local_rx_index
        self.remote_rx_index = remote_rx_index
        self.send_key = send_key
        self.recv_key = recv_key
        self.send_seq = 1
        self.rekey_threshold = rekey_threshold
        self.grace_period_sec = grace_period_sec
        self.active_replay_window = AntiReplayWindow(window_size=128)

        # Registro de índices de recepción locales a claves y ventanas anti-replay
        # {rx_index: {"key": bytes, "replay_window": AntiReplayWindow, "expires_at": Optional[float]}}
        self.rx_states: Dict[int, Dict] = {
            self.local_rx_index: {
                "key": self.recv_key,
                "replay_window": self.active_replay_window,
                "expires_at": None,
                "epoch": 1,
            }
        }

        # Estado del proceso de rekeying en el emisor
        self.rekey_in_progress = False
        self.pending_new_send_key: Optional[bytes] = None
        self.pending_new_remote_rx_index: Optional[int] = None
        self.rekey_count = 0

    def needs_rekey(self) -> bool:
        """Determina si la secuencia saliente ha alcanzado el umbral de re-claveo."""
        return self.send_seq >= self.rekey_threshold and not self.rekey_in_progress

    def initiate_rekey(self) -> bytes:
        """
        Inicia el proceso de rotación de claves en el emisor:
        1. Deriva send_key y recv_key para la época N+1.
        2. Genera un nuevo local_rx_index para la nueva época.
        3. Registra el nuevo rx_state en el receptor local.
        4. Empaqueta un objeto OBJ_REKEY_ANNOUNCE con la clave saliente actual.
        """
        next_epoch = self.epoch + 1
        next_send_key = derive_next_epoch_keys(self.send_key, next_epoch)
        next_recv_key = derive_next_epoch_keys(self.recv_key, next_epoch)
        next_local_rx_index = self.local_rx_index + 1000

        # Guardar en pendientes
        self.pending_new_send_key = next_send_key
        self.rekey_in_progress = True

        # Habilitar inmediatamente el nuevo índice de recepción local para poder recibir con la nueva clave
        self.rx_states[next_local_rx_index] = {
            "key": next_recv_key,
            "replay_window": AntiReplayWindow(window_size=128),
            "expires_at": None,
            "epoch": next_epoch,
        }

        # Construir objeto de anuncio de rekey
        rekey_payload = struct.pack("<II", next_epoch, next_local_rx_index)
        obj = IPVN7Object(
            object_type=OBJ_REKEY_ANNOUNCE,
            payload=rekey_payload,
            object_id=9000 + self.rekey_count,
            priority=7  # Urgente
        )

        container = IPVN7Container(
            receiver_index=self.remote_rx_index,
            sequence_number=self.send_seq,
            objects=[obj]
        )
        packet = container.pack(self.send_key)
        self.send_seq += 1
        return packet

    def handle_rekey_announce(self, obj: IPVN7Object) -> bytes:
        """
        El receptor procesa OBJ_REKEY_ANNOUNCE:
        1. Extrae el next_epoch y el nuevo remote_rx_index ofrecido.
        2. Deriva las claves para la nueva época.
        3. Pasa la clave actual a estado de gracia (expira en grace_period_sec).
        4. Habilita el nuevo índice de recepción local y devuelve un OBJ_REKEY_ACK.
        """
        next_epoch, peer_new_rx_index = struct.unpack("<II", obj.payload)
        next_send_key = derive_next_epoch_keys(self.send_key, next_epoch)
        next_recv_key = derive_next_epoch_keys(self.recv_key, next_epoch)
        next_local_rx_index = self.local_rx_index + 1000

        # Marcar la clave de recepción actual con temporizador de gracia
        current_rx = self.rx_states[self.local_rx_index]
        current_rx["expires_at"] = time.time() + self.grace_period_sec

        # Registrar el nuevo estado de recepción
        self.rx_states[next_local_rx_index] = {
            "key": next_recv_key,
            "replay_window": AntiReplayWindow(window_size=128),
            "expires_at": None,
            "epoch": next_epoch,
        }

        # Actualizar claves salientes para la nueva época
        self.send_key = next_send_key
        self.recv_key = next_recv_key
        self.local_rx_index = next_local_rx_index
        self.remote_rx_index = peer_new_rx_index
        self.epoch = next_epoch
        self.send_seq = 1  # Reinicio de contador de secuencia monótono para la nueva clave!
        self.rekey_count += 1

        # Responder con ACK de confirmación
        ack_payload = struct.pack("<II", next_epoch, next_local_rx_index)
        ack_obj = IPVN7Object(
            object_type=OBJ_REKEY_ACK,
            payload=ack_payload,
            object_id=9500 + self.rekey_count,
            priority=7
        )

        ack_container = IPVN7Container(
            receiver_index=self.remote_rx_index,
            sequence_number=self.send_seq,
            objects=[ack_obj]
        )
        packet = ack_container.pack(self.send_key)
        self.send_seq += 1
        return packet

    def handle_rekey_ack(self, obj: IPVN7Object):
        """
        El iniciador procesa el ACK:
        1. Conmuta definitivamente su send_key al nuevo par.
        2. Pone la clave de recepción previa en periodo de gracia.
        3. Reinicia su secuencia send_seq a 1.
        """
        next_epoch, peer_new_rx_index = struct.unpack("<II", obj.payload)
        current_rx = self.rx_states[self.local_rx_index]
        current_rx["expires_at"] = time.time() + self.grace_period_sec

        self.send_key = self.pending_new_send_key
        self.local_rx_index = self.local_rx_index + 1000
        self.remote_rx_index = peer_new_rx_index
        self.epoch = next_epoch
        self.send_seq = 1  # Reinicio de contador de secuencia
        self.rekey_in_progress = False
        self.rekey_count += 1

    def send_data(self, obj: IPVN7Object) -> bytes:
        """Empaqueta un objeto de datos usando la clave activa de transmisión."""
        container = IPVN7Container(
            receiver_index=self.remote_rx_index,
            sequence_number=self.send_seq,
            objects=[obj]
        )
        packet = container.pack(self.send_key)
        self.send_seq += 1
        return packet

    def receive_packet(self, raw_data: bytes) -> Optional[List[IPVN7Object]]:
        """
        Procesa un datagrama entrante:
        1. Inspecciona el receiver_index del encabezado en texto plano.
        2. Busca si existe una clave activa o en periodo de gracia para ese índice.
        3. Si la clave ha expirado por superar la ventana de gracia, la descarta silenciosamente.
        4. Descifra, autentica AEAD, verifica anti-replay y entrega los objetos.
        """
        self._purge_expired_keys()

        if len(raw_data) < 32:
            return None

        # Desempaquetar el receiver_index del header de contenedor (bytes 4..8)
        rx_index = struct.unpack("<I", raw_data[4:8])[0]
        state = self.rx_states.get(rx_index)
        if state is None:
            # Clave no encontrada o ya purgada post-gracia: descarte silente
            return None

        # Si tiene expiración fijada, comprobar si ya venció
        if state["expires_at"] is not None and time.time() > state["expires_at"]:
            return None

        container = IPVN7Container.unpack(raw_data, state["key"], replay_window=state["replay_window"])
        if container is None:
            return None

        return container.objects

    def _purge_expired_keys(self):
        """Elimina de forma segura las claves cuya ventana de gracia ha expirado."""
        now = time.time()
        to_del = []
        for idx, state in self.rx_states.items():
            if state["expires_at"] is not None and now > state["expires_at"]:
                to_del.append(idx)
        for idx in to_del:
            del self.rx_states[idx]
