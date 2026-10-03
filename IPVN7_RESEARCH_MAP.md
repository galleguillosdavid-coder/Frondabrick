# IPVN7 — Mapa de Investigación (Tercer Trabajo)
**Documento:** `IPVN7_RESEARCH_MAP.md`  
**Versión Conceptual:** IPVN7-0  
**Estado:** DELIMITACIÓN EPISTÉMICA Y TAXONOMÍA DE INVESTIGACIÓN  
**Fecha:** 2026-10-02  
**Clasificación Epistémica:** CONOCIDO / DESCONOCIDO / POR DEMOSTRAR

---

## 1. Propósito del Mapa de Investigación

Para evitar el sesgo de confirmación y la invención de resultados, este mapa clasifica el estado del conocimiento técnico en tres categorías mutuamente excluyentes y define la lista ordenada de investigaciones necesarias para avanzar de forma científica.

---

## 2. Categoría I: CONOCIDO
*Cosas que ya están demostradas, estandarizadas y documentadas externamente en la ingeniería de redes moderna.*

1. **Inseguridad del socket rígido tradicional:**  
   La vinculación estricta de un socket TCP a la 4-tupla $(\text{IP}_\text{src}, \text{Port}_\text{src}, \text{IP}_\text{dst}, \text{Port}_\text{dst})$ colapsa ante la movilidad de red (cambio de celda o Wi-Fi) y requiere capas superiores complejas para restaurar estado.
2. **Propiedades formales del Noise Protocol Framework:**  
   Patrones como `Noise_IK` (emisor conoce la clave estática del receptor; 1-RTT) y `Noise_XX` (autenticación mutua sin conocimiento previo; 1.5-RTT) ofrecen seguridad formalmente probada contra ataques de hombre en el medio (MITM), confidencialidad, autenticación mutua y secreto perfecto hacia adelante (*PFS*).
3. **Eficiencia del Cryptokey Routing (WireGuard):**  
   Asociar claves públicas de pares directamente con sus direcciones IP de túnel y actualizar dinámicamente el endpoint UDP con cada paquete autenticado entrante permite roaming sin interrupciones con mínimo código.
4. **Peligros de la fragmentación en Capa de Red (IPv4/IPv6):**  
   La fragmentación IP intermedia es descartada por gran parte de los firewalls y middleboxes modernos en Internet; la pérdida de un solo fragmento invalida el datagrama completo. Todo protocolo moderno sobre UDP debe evitar fragmentar paquetes en L3.
5. **Ineficiencia del Broadcast en Redes Inalámbricas:**  
   Las tramas de broadcast y multicast en redes 802.11 (Wi-Fi) se transmiten a la tasa de modulación básica más baja para garantizar cobertura, consumiendo desproporcionadamente tiempo de aire (*airtime*) y agotando baterías de dispositivos móviles y de bajo consumo.
6. **Mapeo de NATs y Firewalls (STUN/TURN/ICE):**  
   NATs de tipo cono completo o restringido por puerto permiten conexión directa tras perforación (*hole punching*), pero NATs simétricos (habituales en redes móviles y corporativas) hacen inviable la conexión P2P directa sin un servidor de relevo (*Relay*).
7. **Sobrecarga fija de capas de transporte:**  
   - IPv4: 20 bytes mínimos.  
   - IPv6: 40 bytes fijos.  
   - UDP: 8 bytes fijos.  
   - Encabezado AEAD (Poly1305 o GCM tag): 16 bytes fijos.
8. **Protección Anti-Reflexión mediante Reto Criptográfico:**  
   La validación de camino con nonces de 64 bits (`PATH_CHALLENGE` / `PATH_RESPONSE` de 40B) previene que endpoints no verificados sean usados como vectores de amplificación DoS, limitando el factor de amplificación a $\le 1.0\times$ (RFC 9000).
9. **Desacoplamiento de Cabeza de Línea con Scheduler de Salida:**  
   La intercalación atómica de fragmentos de objeto junto con un planificador de salida con colas de prioridad estricta en el emisor erradica el bloqueo Head-of-Line a nivel de transporte (reducción $> 95\%$ de latencia HoL).

---

## 3. Categoría II: DESCONOCIDO
*Preguntas abiertas, trade-offs no medidos y límites operacionales no resueltos por la teoría inicial.*

1. **Atravesamiento de NAT Simétrico sin Servidor Centralizado Fijo:**  
   ¿Cómo pueden dos nodos IPVN7 situados tras NATs simétricos hostiles coordinar un relevo (*Relay*) de forma descentralizada sin un servidor STUN/TURN comercial permanente?
2. **Control de Congestión Nativo Desacoplado del Camino:**  
   Si una sesión IPVN7 migra abruptamente de Wi-Fi (100 Mbps, 5ms RTT) a Celular 3G/4G (5 Mbps, 80ms RTT), ¿cómo debe reaccionar el estimador de ancho de banda y la ventana de congestión para evitar bufferbloat instantáneo en la nueva interfaz?
3. **Escalabilidad de Enrutamiento por Identidad de Nodo:**  
   Para una red con $> 10,000$ nodos móviles, ¿cuál es el coste en ancho de banda y latencia de mantener una tabla de enrutamiento DHT (Kademlia/Chord) sobre identificadores de 256 bits?
4. **Footprint y viabilidad en microcontroladores de 32 bits ultra-restringidos:**  
   ¿Puede un microcontrolador Cortex-M0+ con 16 KB de RAM y 64 KB de Flash ejecutar la pila mínima de IPVN7 (Noise Handshake + ChaCha20 + framing) manteniendo buffers de trabajo para la aplicación?

---

## 4. Categoría III: ESTADO DE HIPÓTESIS / DEMOSTRACIONES

*Matriz viva de progreso de afirmaciones arquitectónicas.*

1. **H-DEM-01: Migración de Camino sin Disrupción de Aplicación:**  
   $$\boxed{\text{DEMOSTRADO (EXP-03 + EXP-07)}}$$  
   Asimilación de nuevo endpoint en 0-RTT local, y validación criptográfica anti-secuestro en 1.0 RTT mediante reto `PKT_PATH_CHALLENGE` con factor de amplificación $0.48\times \le 1.0\times$.
2. **H-DEM-02: Eficiencia Comparada de Framing frente a HTTP/2 sobre TLS:**  
   $$\boxed{\text{DEMOSTRADO (EXP-01)}}$$  
   Overhead de 40B frente a 90B de HTTP/2+TLS. Ahorro relativo de +26.2% a 16B de payload.
3. **H-DEM-03: Reducción de Ruido de Señalización en Red Local:**  
   $$\boxed{\text{INFERENCIA / MODELO TEÓRICO (EXP-04)}}$$  
   Modelo numérico de red silenciosa. Pendiente validación empírica en socket con costo de sondeo de descubrimiento inicial.
4. **H-DEM-04: Robustez ante Inyección, Corrupción y Replay:**  
   $$\boxed{\text{DEMOSTRADO (EXP-02 + EXP-06)}}$$  
   100.0% de descarte silente ante 2,000 datagramas de datos corruptos y 1,000 datagramas de handshake corruptos, con ventana anti-replay y vinculación estricta de cabecera AAD.
5. **H-DEM-05: Prevención de Head-of-Line Blocking a Nivel de Transporte:**  
   $$\boxed{\text{DEMOSTRADO (EXP-05 + EXP-08)}}$$  
   Intercalación de fragmentos a nivel de Objeto y planificador de colas de salida (`IPVN7EgressScheduler`), reduciendo la latencia de entrega urgente en un 98.9% (de 534ms a 5.6ms).
6. **H-DEM-06: Coexistencia y Transparencia en Middleboxes Reales:**  
   $$\boxed{\text{HIPÓTESIS / PENDIENTE}}$$  
   Requiere pruebas de laboratorio con routers NAT comerciales y variaciones de MTU.

---

## 5. Lista de Investigaciones Necesarias

Para responder a lo desconocido y demostrar lo postulado, se establece la siguiente secuencia metodológica de investigación:

| ID | Investigación | Objetivo Principal | Método / Herramienta | Entregable Esperado |
| :---: | :--- | :--- | :--- | :--- |
| **INV-01** | **Diseño Binario de Cabecera Mínima** | Determinar la distribución de bits óptima para el Contenedor y el Objeto. | Modelado matemático de campos y cálculo de alineación de memoria (32/64 bits). | Especificación binaria de cabecera (`IPVN7_PACKET_FORMAT.md`). |
| **INV-02** | **Selección de Patrón Noise Framework** | Elegir formalmente el handshake adecuado (Noise_IK vs Noise_XX) para IPVN7. | Análisis de matrices de seguridad de Noise Protocol y trade-off de RTT vs anonimato. | Dictamen técnico de handshake y protocolo de claves. |
| **INV-03** | **Benchmarking de Primitivas Criptográficas** | Medir ciclos de CPU y consumo de memoria de ChaCha20-Poly1305 vs AES-GCM. | Micro-benchmarks en Python y C simulado en entornos controlados. | Tabla de costos criptográficos por KB transmitido. |
| **INV-04** | **Estrategia de Fragmentación de Objetos** | Comparar fragmentación de Objeto en capa superior vs delegación a MTU fijo. | Simulación de pérdida de paquetes con pérdida uniforme y ráfagas (Gilbert-Elliott). | Algoritmo de fragmentación y reensamblaje mínimo. |
| **INV-05** | **Protocolo de Verificación de Migración de Camino** | Definir el mecanismo anti-spoofing para actualización de endpoint remoto. | Análisis de vectores de secuestro y diseño de reto-respuesta de 1 paquete. | Especificación del frame `PATH_MIGRATE` / `PATH_CONFIRM`. |

---

> [!NOTE]
> **Conclusión del Mapa de Investigación:**  
> Ninguna de las afirmaciones de la Categoría III ("Por Demostrar") puede darse por sentada hasta que los experimentos detallados en el siguiente trabajo (`IPVN7_EXPERIMENT_PLAN.md`) sean ejecutados y medidos.
