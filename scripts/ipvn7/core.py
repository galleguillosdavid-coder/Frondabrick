#!/usr/bin/env python3
"""
IPVN7 Core — Implementación de Laboratorio del Protocolo Mínimo (v0)
Módulo de ingeniería para pruebas experimentales (EXP-IPVN7-01 a EXP-IPVN7-05).
Implementa:
- Framing y serialización binaria de Objetos y Contenedores (IPVN7_BINARY_SPEC_v0.md)
- Cifrado autenticado AEAD estándar (ChaCha20-Poly1305, RFC 8439)
- Ventana deslizante anti-replay (128 posiciones)
- Principio de descarte silente ante datos corruptos o manipulados
"""

import struct
from typing import List, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.exceptions import InvalidTag

# Constantes del Protocolo IPVN7-v0
MAGIC_BYTE = 0x77  # 'w' - IPVN7 Wire Format v0
CONTAINER_HEADER_FORMAT = "<BBHIQ"
CONTAINER_HEADER_SIZE = struct.calcsize(CONTAINER_HEADER_FORMAT)  # 16 bytes
AEAD_TAG_SIZE = 16  # Poly1305 tag
OBJECT_HEADER_FORMAT = "<BBHI"
OBJECT_HEADER_SIZE = struct.calcsize(OBJECT_HEADER_FORMAT)  # 8 bytes

# Tipos de Paquete de Contenedor
PKT_DATA = 0x01
PKT_HANDSHAKE_INIT = 0x02
PKT_HANDSHAKE_RESP = 0x03
PKT_PATH_CHALLENGE = 0x04
PKT_PATH_RESPONSE = 0x05

# Tipos de Objeto
OBJ_RAW_BYTES = 0x01
OBJ_STRUCTURED_TELEMETRY = 0x02
OBJ_TEXT_MESSAGE = 0x03
OBJ_FILE_FRAGMENT = 0x04
OBJ_RPC_COMMAND = 0x05
OBJ_RPC_RESPONSE = 0x06


class AntiReplayWindow:
    """
    Ventana deslizante anti-replay de 128 posiciones para números de secuencia de 64 bits.
    Utiliza un bitmask entero para validación y actualización en O(1).
    """
    def __init__(self, window_size: int = 128):
        self.window_size = window_size
        self.max_seq = 0
        self.bitmap = 0

    def can_accept(self, seq: int) -> bool:
        """
        Comprobación provisional: verifica si el número de secuencia es válido y no visto.
        NO actualiza el estado interno (evita envenenamiento DoS por paquetes no autenticados).
        """
        if seq == 0:
            return False

        if seq > self.max_seq:
            return True
        else:
            diff = self.max_seq - seq
            if diff >= self.window_size:
                return False
            return (self.bitmap & (1 << diff)) == 0

    def commit(self, seq: int) -> None:
        """
        Compromiso de secuencia: se invoca ÚNICAMENTE después de que el tag AEAD
        ha sido verificado con éxito (RFC 4303 / WireGuard anti-DoS principle).
        """
        if seq > self.max_seq:
            diff = seq - self.max_seq
            if diff < self.window_size:
                self.bitmap = (self.bitmap << diff) | 1
            else:
                self.bitmap = 1
            self.max_seq = seq
        else:
            diff = self.max_seq - seq
            if diff < self.window_size:
                self.bitmap |= (1 << diff)

    def check_and_update(self, seq: int) -> bool:
        """Método de conveniencia atómico para pruebas unitarias de ventana aislada."""
        if not self.can_accept(seq):
            return False
        self.commit(seq)
        return True


class IPVN7Object:
    """
    Representa una unidad lógica de información en IPVN7 (Mensaje, Telemetría, Comando, etc.).
    Encabezado: 8 bytes (<BBHI).
    """
    def __init__(self, object_type: int, payload: bytes, object_id: int = 0, priority: int = 4, flags: int = 0):
        if len(payload) > 65535:
            raise ValueError(f"El payload del objeto excede el límite de 65535 bytes: {len(payload)}")
        self.object_type = object_type
        self.priority = priority & 0x07
        self.flags = (flags & 0x1F) | (self.priority << 5)
        self.payload = payload
        self.object_id = object_id

    def pack(self) -> bytes:
        header = struct.pack(OBJECT_HEADER_FORMAT, self.object_type, self.flags, len(self.payload), self.object_id)
        return header + self.payload

    @classmethod
    def unpack(cls, data: bytes) -> Tuple["IPVN7Object", bytes]:
        if len(data) < OBJECT_HEADER_SIZE:
            raise ValueError(f"Datos insuficientes para cabecera de objeto ({len(data)} < {OBJECT_HEADER_SIZE})")
        obj_type, flags, payload_len, obj_id = struct.unpack(OBJECT_HEADER_FORMAT, data[:OBJECT_HEADER_SIZE])
        priority = (flags >> 5) & 0x07
        raw_flags = flags & 0x1F
        total_len = OBJECT_HEADER_SIZE + payload_len
        if len(data) < total_len:
            raise ValueError(f"Payload truncado: esperado {payload_len}, disponible {len(data) - OBJECT_HEADER_SIZE}")
        payload = data[OBJECT_HEADER_SIZE:total_len]
        remaining = data[total_len:]
        obj = cls(object_type=obj_type, payload=payload, object_id=obj_id, priority=priority, flags=raw_flags)
        return obj, remaining


class IPVN7Container:
    """
    Representa la unidad atómica de transporte sobre el medio (UDP).
    Encabezado: 16 bytes (<BBHIQ).
    Carga: Cifrada y autenticada mediante ChaCha20-Poly1305 (RFC 8439).
    Tag: 16 bytes al final del datagrama.
    """
    def __init__(self, receiver_index: int, sequence_number: int, objects: List[IPVN7Object], packet_type: int = PKT_DATA):
        self.magic = MAGIC_BYTE
        self.packet_type = packet_type
        self.reserved = 0x0000
        self.receiver_index = receiver_index
        self.sequence_number = sequence_number
        self.objects = objects

    def pack(self, key: bytes) -> bytes:
        if len(key) != 32:
            raise ValueError(f"La clave ChaCha20-Poly1305 debe ser de exactamente 32 bytes (recibido {len(key)})")

        # 1. Serializar la concatenación de objetos
        raw_objects = b"".join(obj.pack() for obj in self.objects)

        # 2. Construir cabecera de 16 bytes (AAD)
        header = struct.pack(
            CONTAINER_HEADER_FORMAT,
            self.magic,
            self.packet_type,
            self.reserved,
            self.receiver_index,
            self.sequence_number
        )

        # 3. Construir Nonce estándar de 96 bits (4 bytes ceros + 8 bytes counter en Little-Endian)
        nonce = b"\x00\x00\x00\x00" + struct.pack("<Q", self.sequence_number)

        # 4. Cifrado AEAD (el método encrypt de cryptography anexa el tag de 16 bytes al final)
        cipher = ChaCha20Poly1305(key)
        ciphertext_and_tag = cipher.encrypt(nonce, raw_objects, header)

        return header + ciphertext_and_tag

    @classmethod
    def unpack(cls, raw_data: bytes, key: bytes, replay_window: Optional[AntiReplayWindow] = None) -> Optional["IPVN7Container"]:
        """
        Decodifica y valida un contenedor IPVN7.
        Aplica el Principio de Descarte Silente: ante cualquier error de validación, tag inválido,
        número de magia incorrecto o secuencia fuera de ventana, retorna None de forma silente.
        """
        # Mínimo absoluto: 16 bytes header + 16 bytes tag AEAD = 32 bytes
        min_size = CONTAINER_HEADER_SIZE + AEAD_TAG_SIZE
        if len(raw_data) < min_size:
            return None

        # 1. Inspeccionar encabezado
        magic, pkt_type, reserved, rx_index, seq_num = struct.unpack(CONTAINER_HEADER_FORMAT, raw_data[:CONTAINER_HEADER_SIZE])
        if magic != MAGIC_BYTE:
            return None

        # 2. Comprobación provisional anti-replay (sin actualizar estado)
        if replay_window is not None:
            if not replay_window.can_accept(seq_num):
                return None

        # 3. Descifrar y autenticar AEAD (ChaCha20-Poly1305)
        header = raw_data[:CONTAINER_HEADER_SIZE]
        ciphertext_and_tag = raw_data[CONTAINER_HEADER_SIZE:]
        nonce = b"\x00\x00\x00\x00" + struct.pack("<Q", seq_num)

        try:
            cipher = ChaCha20Poly1305(key)
            plaintext = cipher.decrypt(nonce, ciphertext_and_tag, header)
        except InvalidTag:
            # Fallo de autenticación o manipulación de bits: descarte silente
            # El estado de la ventana anti-replay NO fue alterado
            return None
        except Exception:
            return None

        # 4. Si la autenticación fue exitosa, comprometer el número de secuencia en la ventana
        if replay_window is not None:
            replay_window.commit(seq_num)

        # 4. Deserializar los objetos contenidos en el texto plano
        objects = []
        stream = plaintext
        while stream:
            try:
                obj, stream = IPVN7Object.unpack(stream)
                objects.append(obj)
            except Exception:
                # Error en el parsing interno de objetos descifrados
                return None

        container = cls(receiver_index=rx_index, sequence_number=seq_num, objects=objects, packet_type=pkt_type)
        return container
