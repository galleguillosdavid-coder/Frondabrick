"""
IPVN7 Cryptographic Handshake Engine (Noise_IK Pattern)
Implementa el apretón de manos formal en 1 RTT (Curve25519 / ChaCha20-Poly1305 / HKDF-SHA256).

Garantiza:
1. Autenticación mutua de identidad mediante claves públicas estáticas X25519.
2. Derivación de claves de sesión efímeras con Secreto Perfecto hacia Adelante (PFS).
3. Descarte silente ante cualquier tag inválido, clave no autorizada o manipulación de bits.
4. Paquetes compactos en el cable: Init (116B) y Resp (60B).
"""

import struct
import time
import os
from typing import Optional, Tuple, Dict
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

from scripts.ipvn7.core import (
    MAGIC_BYTE,
    PKT_HANDSHAKE_INIT,
    PKT_HANDSHAKE_RESP,
    AntiReplayWindow,
)

# Constantes del protocolo Noise_IK para IPVN7
PROTOCOL_NAME = b"Noise_IK_25519_ChaChaPoly_SHA256_IPVN7v0"
HASH_LEN = 32

INIT_HEADER_FORMAT = "<BBHI32s48s28s"
INIT_PACKET_SIZE = struct.calcsize(INIT_HEADER_FORMAT)  # 1 + 1 + 2 + 4 + 32 + 48 + 28 = 116 bytes

RESP_HEADER_FORMAT = "<BBHII32s16s"
RESP_PACKET_SIZE = struct.calcsize(RESP_HEADER_FORMAT)  # 1 + 1 + 2 + 4 + 4 + 32 + 16 = 60 bytes


def sha256(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def kdf(ck: bytes, input_key_material: bytes, num_outputs: int = 2) -> Tuple[bytes, ...]:
    """Derivación de claves HKDF con SHA-256 según especificación Noise."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32 * num_outputs,
        salt=ck,
        info=b"",
    )
    derived = hkdf.derive(input_key_material)
    return tuple(derived[i * 32 : (i + 1) * 32] for i in range(num_outputs))


class IPVN7Session:
    """Representa una sesión criptográfica establecida post-handshake."""
    def __init__(self, local_index: int, remote_index: int, send_key: bytes, recv_key: bytes, peer_static_pub: bytes):
        self.local_index = local_index
        self.remote_index = remote_index
        self.send_key = send_key
        self.recv_key = recv_key
        self.peer_static_pub = peer_static_pub
        self.send_seq = 1
        self.replay_window = AntiReplayWindow(window_size=128)
        self.remote_addr: Optional[Tuple[str, int]] = None
        self.created_at = time.time()


class NoiseIKHandshakeInitiator:
    """Autómata del Iniciador (Cliente) en Noise_IK."""
    def __init__(self, static_priv: X25519PrivateKey, peer_static_pub_bytes: bytes, local_index: int):
        self.static_priv = static_priv
        self.static_pub_bytes = static_priv.public_key().public_bytes_raw()
        self.peer_static_pub_bytes = peer_static_pub_bytes
        self.local_index = local_index
        self.ephemeral_priv: Optional[X25519PrivateKey] = None
        self.chaining_key: bytes = b""
        self.handshake_hash: bytes = b""

    def create_initiation_packet(self) -> bytes:
        """Genera el datagrama PKT_HANDSHAKE_INIT (116 bytes)."""
        self.ephemeral_priv = X25519PrivateKey.generate()
        e_pub = self.ephemeral_priv.public_key().public_bytes_raw()

        # Construir prefijo de cabecera de 8 bytes (Magic, Type, Reserved, Sender_Index)
        header_prefix = struct.pack("<BBHI", MAGIC_BYTE, PKT_HANDSHAKE_INIT, 0x0000, self.local_index)

        # Inicializar Hash y Chaining Key
        h = sha256(PROTOCOL_NAME)
        ck = h
        # MixHash(prologue)
        h = sha256(h + b"IPVN7_PROLOGUE_v0")
        # MixHash(header_prefix) - Autentica estrictamente los 8 bytes iniciales de cabecera
        h = sha256(h + header_prefix)
        # MixHash(rs)
        h = sha256(h + self.peer_static_pub_bytes)
        # MixHash(e)
        h = sha256(h + e_pub)

        # MixKey(DH(e, rs))
        peer_static_pub = X25519PublicKey.from_public_bytes(self.peer_static_pub_bytes)
        dh1 = self.ephemeral_priv.exchange(peer_static_pub)
        ck, k1 = kdf(ck, dh1, num_outputs=2)

        # EncryptAndHash(s) -> 32B pub + 16B tag = 48B
        cipher1 = ChaCha20Poly1305(k1)
        nonce1 = b"\x00" * 12
        encrypted_static = cipher1.encrypt(nonce1, self.static_pub_bytes, h)
        h = sha256(h + encrypted_static)

        # MixKey(DH(s, rs))
        dh2 = self.static_priv.exchange(peer_static_pub)
        ck, k2 = kdf(ck, dh2, num_outputs=2)

        # EncryptAndHash(timestamp) -> 12B timestamp + 16B tag = 28B
        timestamp_bytes = struct.pack("<Qd", int(time.time()), time.time())[:12]
        cipher2 = ChaCha20Poly1305(k2)
        nonce2 = b"\x00" * 12
        encrypted_timestamp = cipher2.encrypt(nonce2, timestamp_bytes, h)
        h = sha256(h + encrypted_timestamp)

        self.chaining_key = ck
        self.handshake_hash = h

        # Empaquetar datagrama
        packet = header_prefix + e_pub + encrypted_static + encrypted_timestamp
        return packet

    def process_response_packet(self, data: bytes) -> Optional[IPVN7Session]:
        """Procesa PKT_HANDSHAKE_RESP y finaliza la derivación de claves."""
        if len(data) != RESP_PACKET_SIZE:
            return None

        magic, pkt_type, reserved, resp_index, rx_index, resp_e_pub, encrypted_empty = struct.unpack(
            RESP_HEADER_FORMAT, data
        )

        if magic != MAGIC_BYTE or pkt_type != PKT_HANDSHAKE_RESP or reserved != 0x0000 or rx_index != self.local_index:
            return None

        # Autenticar los 12 bytes de cabecera de respuesta en el hash
        resp_header_prefix = struct.pack("<BBHII", magic, pkt_type, reserved, resp_index, rx_index)

        h = self.handshake_hash
        ck = self.chaining_key

        # MixHash(resp_header_prefix)
        h = sha256(h + resp_header_prefix)

        # MixHash(re)
        h = sha256(h + resp_e_pub)

        # MixKey(DH(e, re))
        resp_e_pub_obj = X25519PublicKey.from_public_bytes(resp_e_pub)
        dh3 = self.ephemeral_priv.exchange(resp_e_pub_obj)
        ck, temp_k1 = kdf(ck, dh3, num_outputs=2)

        # MixKey(DH(s, re))
        dh4 = self.static_priv.exchange(resp_e_pub_obj)
        ck, k3 = kdf(ck, dh4, num_outputs=2)

        # DecryptAndHash(empty) -> verificar autenticidad del respondedor
        cipher3 = ChaCha20Poly1305(k3)
        nonce3 = b"\x00" * 12
        try:
            cipher3.decrypt(nonce3, encrypted_empty, h)
        except InvalidTag:
            return None
        except Exception:
            return None

        h = sha256(h + encrypted_empty)

        # Derivación final de claves de sesión (Transport Keys)
        # Initiator: send_key = k_send, recv_key = k_recv
        k_send, k_recv = kdf(ck, b"", num_outputs=2)

        # Borrado seguro de clave efímera para Forward Secrecy
        self.ephemeral_priv = None

        session = IPVN7Session(
            local_index=self.local_index,
            remote_index=resp_index,
            send_key=k_send,
            recv_key=k_recv,
            peer_static_pub=self.peer_static_pub_bytes,
        )
        return session


class NoiseIKHandshakeResponder:
    """Autómata del Respondedor (Servidor) en Noise_IK."""
    def __init__(self, static_priv: X25519PrivateKey, local_index: int, authorized_peers: Dict[bytes, str]):
        self.static_priv = static_priv
        self.static_pub_bytes = static_priv.public_key().public_bytes_raw()
        self.local_index = local_index
        self.authorized_peers = authorized_peers  # {public_key_bytes: peer_name}

    def process_initiation_and_respond(self, data: bytes) -> Tuple[Optional[bytes], Optional[IPVN7Session]]:
        """
        Procesa PKT_HANDSHAKE_INIT. Si es válido y autorizado, genera PKT_HANDSHAKE_RESP y la sesión.
        Aplica descarte silente ante cualquier anomalía o falta de autorización.
        """
        if len(data) != INIT_PACKET_SIZE:
            return None, None

        magic, pkt_type, reserved, init_sender_idx, init_e_pub, enc_static, enc_ts = struct.unpack(
            INIT_HEADER_FORMAT, data
        )

        if magic != MAGIC_BYTE or pkt_type != PKT_HANDSHAKE_INIT or reserved != 0x0000:
            return None, None

        header_prefix = struct.pack("<BBHI", magic, pkt_type, reserved, init_sender_idx)

        # Inicializar Hash y Chaining Key
        h = sha256(PROTOCOL_NAME)
        ck = h
        h = sha256(h + b"IPVN7_PROLOGUE_v0")
        h = sha256(h + header_prefix)
        h = sha256(h + self.static_pub_bytes)
        h = sha256(h + init_e_pub)

        # MixKey(DH(rs, e))
        try:
            init_e_pub_obj = X25519PublicKey.from_public_bytes(init_e_pub)
        except Exception:
            return None, None

        dh1 = self.static_priv.exchange(init_e_pub_obj)
        ck, k1 = kdf(ck, dh1, num_outputs=2)

        # DecryptAndHash(s)
        cipher1 = ChaCha20Poly1305(k1)
        nonce1 = b"\x00" * 12
        try:
            initiator_static_pub = cipher1.decrypt(nonce1, enc_static, h)
        except InvalidTag:
            return None, None
        except Exception:
            return None, None

        # Verificación estricta de autorización de identidad del Iniciador
        if initiator_static_pub not in self.authorized_peers:
            # Identidad no autorizada: descarte silente absoluto
            return None, None

        h = sha256(h + enc_static)

        # MixKey(DH(rs, s))
        initiator_static_pub_obj = X25519PublicKey.from_public_bytes(initiator_static_pub)
        dh2 = self.static_priv.exchange(initiator_static_pub_obj)
        ck, k2 = kdf(ck, dh2, num_outputs=2)

        # DecryptAndHash(timestamp)
        cipher2 = ChaCha20Poly1305(k2)
        nonce2 = b"\x00" * 12
        try:
            decrypted_ts = cipher2.decrypt(nonce2, enc_ts, h)
        except InvalidTag:
            return None, None
        except Exception:
            return None, None

        h = sha256(h + enc_ts)

        # Generar clave efímera del Respondedor
        resp_e_priv = X25519PrivateKey.generate()
        resp_e_pub = resp_e_priv.public_key().public_bytes_raw()

        # Construir prefijo de cabecera de 12 bytes de respuesta
        resp_header_prefix = struct.pack(
            "<BBHII",
            MAGIC_BYTE,
            PKT_HANDSHAKE_RESP,
            0x0000,
            self.local_index,
            init_sender_idx
        )

        # MixHash(resp_header_prefix)
        h = sha256(h + resp_header_prefix)

        # MixHash(re)
        h = sha256(h + resp_e_pub)

        # MixKey(DH(re, e))
        dh3 = resp_e_priv.exchange(init_e_pub_obj)
        ck, temp_k1 = kdf(ck, dh3, num_outputs=2)

        # MixKey(DH(re, s))
        dh4 = resp_e_priv.exchange(initiator_static_pub_obj)
        ck, k3 = kdf(ck, dh4, num_outputs=2)

        # EncryptAndHash(empty) -> 16B tag
        cipher3 = ChaCha20Poly1305(k3)
        nonce3 = b"\x00" * 12
        encrypted_empty = cipher3.encrypt(nonce3, b"", h)
        h = sha256(h + encrypted_empty)

        # Derivación final de claves de sesión (Transport Keys)
        # Para el Responder: su send_key es el recv_key del iniciador y viceversa
        k_init_send, k_init_recv = kdf(ck, b"", num_outputs=2)

        response_packet = resp_header_prefix + resp_e_pub + encrypted_empty

        session = IPVN7Session(
            local_index=self.local_index,
            remote_index=init_sender_idx,
            send_key=k_init_recv,  # Envia con lo que el iniciador recibe
            recv_key=k_init_send,  # Recibe con lo que el iniciador envía
            peer_static_pub=initiator_static_pub,
        )

        return response_packet, session
