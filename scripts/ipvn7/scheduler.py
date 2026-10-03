"""
IPVN7 Egress Priority Scheduler (Anti-Head-of-Line Blocking for Real Networks)
Implementa un planificador de salida con colas de prioridad estricta (Prioridades 0 a 7)
y despacho temporizado (Pacing) para evitar que transferencias masivas fragmentadas
saturen el buffer del socket del sistema operativo y bloqueen comandos urgentes.
"""

import time
import queue
import threading
from typing import Optional, Tuple, Dict, List, Callable
from dataclasses import dataclass, field

from scripts.ipvn7.core import IPVN7Object, IPVN7Container


@dataclass(order=True)
class PrioritizedItem:
    priority_key: int  # En Python heapq/PriorityQueue, menor valor = mayor prioridad.
    enqueue_time: float
    container_or_obj: any = field(compare=False)
    destination: Tuple[str, int] = field(compare=False)


class IPVN7EgressScheduler:
    """
    Planificador de salida con colas de prioridad estricta (0..7).
    Prioridad 7 = Urgente / Control (despacho inmediato).
    Prioridad 4 = Normal / Telemetría.
    Prioridad 1 = Datos masivos / Archivos.
    Prioridad 0 = Fondo / Mantenimiento.
    """
    def __init__(self, send_func: Callable[[bytes, Tuple[str, int]], None], max_packets_per_sec: float = 50.0):
        self.send_func = send_func
        self.packet_interval_sec = 1.0 / max_packets_per_sec if max_packets_per_sec > 0 else 0.0
        # PriorityQueue es thread-safe en Python
        self.queue: queue.PriorityQueue = queue.PriorityQueue()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.total_dispatched = 0
        self.dispatch_timestamps: List[Tuple[int, float]] = []  # (priority, timestamp)

    def enqueue(self, raw_packet: bytes, destination: Tuple[str, int], priority: int = 4):
        """
        Encola un paquete serializado para despacho.
        priority: 0 a 7. Internamente se mapea priority_key = (7 - priority)
        para que Prioridad 7 tenga la clave 0 (máxima prioridad de despacho).
        """
        priority = max(0, min(7, priority))
        priority_key = 7 - priority
        item = PrioritizedItem(
            priority_key=priority_key,
            enqueue_time=time.time(),
            container_or_obj=raw_packet,
            destination=destination
        )
        self.queue.put(item)

    def start(self):
        """Inicia el despachador en un hilo de fondo."""
        self.running = True
        self.worker_thread = threading.Thread(target=self._pacer_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        """Detiene el planificador."""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)

    def _pacer_loop(self):
        while self.running:
            try:
                # Esperar hasta que haya un elemento con timeout para poder chequear self.running
                item: PrioritizedItem = self.queue.get(timeout=0.05)
            except queue.Empty:
                continue

            # Despachar el paquete más prioritario
            self.send_func(item.container_or_obj, item.destination)
            dispatch_time = time.time()
            priority = 7 - item.priority_key
            self.dispatch_timestamps.append((priority, dispatch_time))
            self.total_dispatched += 1
            self.queue.task_done()

            # Pacing: respetar el intervalo mínimo de emisión para no desbordar el socket
            if self.packet_interval_sec > 0:
                time.sleep(self.packet_interval_sec)
