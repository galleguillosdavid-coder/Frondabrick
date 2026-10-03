"""
IPVN7 NAT Traversal & Hole-Punching Module (EXP-IPVN7-10)
=========================================================
Implements:
1. NAT Behavioral Models:
   - Full Cone (Endpoint-Independent Mapping & Filtering)
   - Address-Restricted Cone (Endpoint-Independent Mapping, Address-Dependent Filtering)
   - Port-Restricted Cone (Endpoint-Independent Mapping, Address-and-Port-Dependent Filtering)
   - Symmetric NAT (Endpoint-Dependent Mapping)
2. Rendezvous / Signaling Server emulation for initial external coordinate exchange.
3. IPVN7 UDP Hole-Punching Protocol:
   - PKT_NAT_PUNCH (40 bytes fixed, authenticated)
   - PKT_NAT_KEEPALIVE (40 bytes fixed, authenticated)
4. Adaptive Keepalive Manager:
   - Quiescence detection: 0 keepalive overhead during active data flow.
   - Mapping timeout defense: Periodic minimal pulse only when idle.
"""

import time
import os
import struct
from enum import Enum
from typing import Dict, Tuple, Optional, List
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

# Packet Types for NAT Traversal in Container Header (Magic = 0x77)
MAGIC_BYTE = 0x77
PKT_NAT_PUNCH = 0x07
PKT_NAT_KEEPALIVE = 0x08

class NATType(Enum):
    FULL_CONE = 1
    RESTRICTED_CONE = 2
    PORT_RESTRICTED_CONE = 3
    SYMMETRIC = 4


class NATMapping:
    """Represents a NAT translation entry."""
    def __init__(self, internal_addr: Tuple[str, int], external_addr: Tuple[str, int], target_addr: Tuple[str, int]):
        self.internal_addr = internal_addr
        self.external_addr = external_addr
        self.target_addr = target_addr
        self.created_at = time.time()
        self.last_activity = time.time()
        # Allowed peers to send traffic back to external_addr
        # Set of (ip) for Restricted Cone, Set of (ip, port) for Port-Restricted
        self.allowed_ips = {target_addr[0]}
        self.allowed_endpoints = {target_addr}


class NATRouter:
    """
    Emulates an enterprise / residential stateful NAT router.
    """
    def __init__(self, public_ip: str, nat_type: NATType, mapping_timeout_sec: float = 30.0):
        self.public_ip = public_ip
        self.nat_type = nat_type
        self.mapping_timeout_sec = mapping_timeout_sec
        self.next_external_port = 40000
        # Mappings: internal_addr -> NATMapping (for Cone NATs)
        # or (internal_addr, target_addr) -> NATMapping (for Symmetric NAT)
        self.cone_mappings: Dict[Tuple[str, int], NATMapping] = {}
        self.symmetric_mappings: Dict[Tuple[Tuple[str, int], Tuple[str, int]], NATMapping] = {}
        self.external_port_map: Dict[int, NATMapping] = {}

    def _allocate_external_port(self) -> int:
        p = self.next_external_port
        self.next_external_port += 1
        return p

    def purge_expired(self, current_time: Optional[float] = None):
        """Removes mappings that exceeded idle timeout."""
        now = current_time if current_time is not None else time.time()
        expired_cone = [k for k, m in self.cone_mappings.items() if now - m.last_activity > self.mapping_timeout_sec]
        for k in expired_cone:
            m = self.cone_mappings.pop(k)
            self.external_port_map.pop(m.external_addr[1], None)

        expired_sym = [k for k, m in self.symmetric_mappings.items() if now - m.last_activity > self.mapping_timeout_sec]
        for k in expired_sym:
            m = self.symmetric_mappings.pop(k)
            self.external_port_map.pop(m.external_addr[1], None)

    def outbound_translate(self, src: Tuple[str, int], dst: Tuple[str, int], payload: bytes, current_time: Optional[float] = None) -> Tuple[Tuple[str, int], bytes]:
        """
        Translates outbound packet from internal endpoint 'src' heading to external 'dst'.
        Returns (translated_src_endpoint, payload).
        """
        self.purge_expired(current_time)
        now = current_time if current_time is not None else time.time()

        if self.nat_type in (NATType.FULL_CONE, NATType.RESTRICTED_CONE, NATType.PORT_RESTRICTED_CONE):
            if src not in self.cone_mappings:
                ext_port = self._allocate_external_port()
                ext_addr = (self.public_ip, ext_port)
                mapping = NATMapping(src, ext_addr, dst)
                self.cone_mappings[src] = mapping
                self.external_port_map[ext_port] = mapping
            else:
                mapping = self.cone_mappings[src]
                mapping.last_activity = now
                mapping.allowed_ips.add(dst[0])
                mapping.allowed_endpoints.add(dst)
            return mapping.external_addr, payload

        elif self.nat_type == NATType.SYMMETRIC:
            key = (src, dst)
            if key not in self.symmetric_mappings:
                ext_port = self._allocate_external_port()
                ext_addr = (self.public_ip, ext_port)
                mapping = NATMapping(src, ext_addr, dst)
                self.symmetric_mappings[key] = mapping
                self.external_port_map[ext_port] = mapping
            else:
                mapping = self.symmetric_mappings[key]
                mapping.last_activity = now
            return mapping.external_addr, payload
        else:
            raise ValueError(f"Unknown NAT type: {self.nat_type}")

    def inbound_translate(self, src: Tuple[str, int], dst: Tuple[str, int], payload: bytes, current_time: Optional[float] = None) -> Optional[Tuple[Tuple[str, int], bytes]]:
        """
        Filters and translates inbound packet arriving from external 'src' addressed to 'dst' (public_ip, port).
        Returns (internal_dst_endpoint, payload) or None if filtered/dropped.
        """
        self.purge_expired(current_time)
        now = current_time if current_time is not None else time.time()
        ext_port = dst[1]

        if ext_port not in self.external_port_map:
            return None  # No mapping -> silent drop

        mapping = self.external_port_map[ext_port]

        # Apply filtering rule based on NAT type
        if self.nat_type == NATType.FULL_CONE:
            # Anyone can send to this external port
            mapping.last_activity = now
            return mapping.internal_addr, payload

        elif self.nat_type == NATType.RESTRICTED_CONE:
            # Allowed only if internal endpoint has sent to src[0] (IP)
            if src[0] in mapping.allowed_ips:
                mapping.last_activity = now
                return mapping.internal_addr, payload
            return None

        elif self.nat_type == NATType.PORT_RESTRICTED_CONE:
            # Allowed only if internal endpoint has sent to src (IP, Port)
            if src in mapping.allowed_endpoints:
                mapping.last_activity = now
                return mapping.internal_addr, payload
            return None

        elif self.nat_type == NATType.SYMMETRIC:
            # Allowed only if mapping target matches sender exactly
            if mapping.target_addr == src:
                mapping.last_activity = now
                return mapping.internal_addr, payload
            return None

        return None


class RendezvousServer:
    """
    Lightweight STUN/Coordination broker.
    Collects reflexive public addresses and relays punch intent.
    Never relays bulk payload traffic.
    """
    def __init__(self, public_ip: str = "203.0.113.1", port: int = 5000):
        self.endpoint = (public_ip, port)
        self.registrations: Dict[int, Tuple[str, int]] = {}  # session_id -> external_addr

    def register(self, session_id: int, external_addr: Tuple[str, int]):
        self.registrations[session_id] = external_addr

    def get_peer(self, session_id: int) -> Optional[Tuple[str, int]]:
        return self.registrations.get(session_id)


def build_nat_punch_packet(session_key: bytes, receiver_index: int, nonce64: int) -> bytes:
    """
    Builds a 40-byte authenticated PKT_NAT_PUNCH datagram:
    - Magic (0x77), Type (0x07), Reserved (0x0000) : 4 bytes
    - Receiver Index                               : 4 bytes
    - Nonce (64 bits)                              : 8 bytes
    - Poly1305 Tag (over the 16 bytes header)      : 16 bytes
    - Zero padding                                 : 8 bytes
    Total: 40 bytes.
    """
    header_aad = struct.pack("<BBHIQ", MAGIC_BYTE, PKT_NAT_PUNCH, 0x0000, receiver_index, nonce64)
    # AEAD tag calculated with nonce constructed from nonce64
    aead_nonce = struct.pack("<IQ", 0, nonce64)
    cipher = ChaCha20Poly1305(session_key)
    # Encrypt empty payload with header as AAD
    ciphertext_and_tag = cipher.encrypt(aead_nonce, b"", header_aad)
    tag = ciphertext_and_tag  # 16 bytes
    # Fixed 40-byte wire layout: 16 bytes header + 16 bytes tag + 8 bytes padding
    return header_aad + tag + b"\x00" * 8


def verify_nat_punch_packet(session_key: bytes, packet: bytes) -> Optional[Tuple[int, int]]:
    """
    Validates a 40-byte PKT_NAT_PUNCH packet.
    Returns (receiver_index, nonce64) or None if invalid.
    """
    if len(packet) != 40:
        return None
    magic, ptype, res, r_idx, nonce64 = struct.unpack("<BBHIQ", packet[:16])
    if magic != MAGIC_BYTE or ptype != PKT_NAT_PUNCH:
        return None
    header_aad = packet[:16]
    tag = packet[16:32]
    aead_nonce = struct.pack("<IQ", 0, nonce64)
    cipher = ChaCha20Poly1305(session_key)
    try:
        cipher.decrypt(aead_nonce, tag, header_aad)
        return (r_idx, nonce64)
    except Exception:
        return None


def build_nat_keepalive_packet(session_key: bytes, receiver_index: int, counter: int) -> bytes:
    """
    Builds a 40-byte authenticated PKT_NAT_KEEPALIVE datagram.
    """
    header_aad = struct.pack("<BBHIQ", MAGIC_BYTE, PKT_NAT_KEEPALIVE, 0x0000, receiver_index, counter)
    aead_nonce = struct.pack("<IQ", 0, counter)
    cipher = ChaCha20Poly1305(session_key)
    tag = cipher.encrypt(aead_nonce, b"", header_aad)
    return header_aad + tag + b"\x00" * 8


def verify_nat_keepalive_packet(session_key: bytes, packet: bytes) -> Optional[Tuple[int, int]]:
    """
    Validates a 40-byte PKT_NAT_KEEPALIVE packet.
    """
    if len(packet) != 40:
        return None
    magic, ptype, res, r_idx, counter = struct.unpack("<BBHIQ", packet[:16])
    if magic != MAGIC_BYTE or ptype != PKT_NAT_KEEPALIVE:
        return None
    header_aad = packet[:16]
    tag = packet[16:32]
    aead_nonce = struct.pack("<IQ", 0, counter)
    cipher = ChaCha20Poly1305(session_key)
    try:
        cipher.decrypt(aead_nonce, tag, header_aad)
        return (r_idx, counter)
    except Exception:
        return None


class IPVN7NATNode:
    """
    An IPVN7 Node operating behind a NAT.
    Supports:
    1. Rendezvous registration.
    2. 1-RTT Hole punching.
    3. Direct communication once punched.
    4. Adaptive Keepalive with Quiescence detection.
    """
    def __init__(self, internal_ip: str, internal_port: int, nat: NATRouter, session_key: bytes, rx_index: int):
        self.internal_endpoint = (internal_ip, internal_port)
        self.nat = nat
        self.session_key = session_key
        self.rx_index = rx_index
        self.peer_endpoint: Optional[Tuple[str, int]] = None
        self.peer_rx_index: Optional[int] = None
        self.last_egress_time = 0.0
        self.keepalive_interval_sec = 15.0  # Send keepalive if idle for 15s
        self.keepalive_counter = 1
        self.punched = False
        self.keepalives_sent = 0

    def register_at_rendezvous(self, server: RendezvousServer, session_id: int):
        # Outbound probe to rendezvous server sets up NAT mapping
        probe_payload = b"REG:" + str(session_id).encode()
        ext_addr, _ = self.nat.outbound_translate(self.internal_endpoint, server.endpoint, probe_payload)
        server.register(session_id, ext_addr)
        return ext_addr

    def initiate_hole_punch(self, peer_ext_addr: Tuple[str, int], peer_rx_index: int) -> bytes:
        """
        Emits PKT_NAT_PUNCH towards peer's external address.
        This opens our outbound NAT state.
        """
        self.peer_endpoint = peer_ext_addr
        self.peer_rx_index = peer_rx_index
        nonce = int.from_bytes(os.urandom(8), "little")
        pkt = build_nat_punch_packet(self.session_key, peer_rx_index, nonce)
        ext_src, wire_pkt = self.nat.outbound_translate(self.internal_endpoint, peer_ext_addr, pkt)
        self.last_egress_time = time.time()
        return wire_pkt

    def receive_packet_from_nat(self, wire_src: Tuple[str, int], wire_pkt: bytes) -> Optional[dict]:
        """
        Processes inbound packet passed through our NAT.
        """
        # Check if it is a punch packet
        punch = verify_nat_punch_packet(self.session_key, wire_pkt)
        if punch:
            self.punched = True
            return {"type": "PUNCH", "sender": wire_src, "rx_index": punch[0], "nonce": punch[1]}

        keepalive = verify_nat_keepalive_packet(self.session_key, wire_pkt)
        if keepalive:
            return {"type": "KEEPALIVE", "sender": wire_src, "counter": keepalive[1]}

        self.punched = True  # Tráfico directo recibido confirma conectividad P2P establecida
        return {"type": "DATA", "sender": wire_src, "payload": wire_pkt}

    def maybe_send_keepalive(self, current_time: Optional[float] = None) -> Optional[bytes]:
        """
        Adaptive Quiescence Keepalive:
        Only emits a keepalive packet if NO egress packet has been sent
        for at least keepalive_interval_sec. If data is actively flowing,
        this produces 0 packets (Quiescent).
        """
        now = current_time if current_time is not None else time.time()
        if not self.punched or not self.peer_endpoint or not self.peer_rx_index:
            return None

        idle_duration = now - self.last_egress_time
        if idle_duration >= self.keepalive_interval_sec:
            pkt = build_nat_keepalive_packet(self.session_key, self.peer_rx_index, self.keepalive_counter)
            self.keepalive_counter += 1
            self.keepalives_sent += 1
            self.last_egress_time = now
            _, wire_pkt = self.nat.outbound_translate(self.internal_endpoint, self.peer_endpoint, pkt, current_time=now)
            return wire_pkt

        return None

    def send_data(self, payload: bytes, current_time: Optional[float] = None) -> bytes:
        """
        Sends ordinary payload; resets the idle keepalive timer.
        """
        if not self.peer_endpoint:
            raise RuntimeError("Peer endpoint unknown")
        self.last_egress_time = current_time if current_time is not None else time.time()
        _, wire_pkt = self.nat.outbound_translate(self.internal_endpoint, self.peer_endpoint, payload, current_time=current_time)
        return wire_pkt
