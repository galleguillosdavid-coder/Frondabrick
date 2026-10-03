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

---

## 3. Categoría II: DESCONOCIDO
*Preguntas abiertas, trade-offs no medidos y límites operacionales no resueltos por la teoría inicial.*

1. **Tamaño mínimo alcanzable de cabecera en IPVN7:**  
   ¿Es viable empaquetar `Session ID` + `Counter` + `Object Framing` + `Tag` en menos de 24–32 bytes sin debilitar la seguridad ni la entropía?
2. **Impacto del descarte silente ante ataques de amplificación:**  
   Si un atacante falsifica la IP de origen en un handshake inicial, ¿puede el nodo IPVN7 protegerse completamente de ser un reflector DoS manteniendo el handshake en 1-RTT sin cookies previas?
3. **Comportamiento de multiplexación sin control de flujo por canal:**  
   Si se simplifica la arquitectura prescindiendo de una máquina de estados de control de flujo por canal (como se propuso en la revisión crítica), ¿en qué grado penaliza un objeto grande (ej. 500 KB) la latencia de un objeto prioritario de 50 bytes en un enlace con ancho de banda restringido (ej. 256 kbps)?
4. **Footprint y viabilidad en microcontroladores de 32 bits ultra-restringidos:**  
   ¿Puede un microcontrolador Cortex-M0+ con 16 KB de RAM y 64 KB de Flash ejecutar la pila mínima de IPVN7 (Noise Handshake + ChaCha20 + framing) manteniendo buffers de trabajo para la aplicación?
5. **Costo de retransmisión a nivel de Objeto vs a nivel de Paquete:**  
   Si un Objeto grande de 10 KB se divide en 9 Contenedores UDP y se pierde 1 Contenedor, ¿es más eficiente retransmitir solo el fragmento faltante o todo el Objeto? ¿Qué complejidad de buffering agrega la retransmisión selectiva en el receptor?

---

## 4. Categoría III: POR DEMOSTRAR
*Afirmaciones y promesas centrales de IPVN7 que NO son hechos hoy y que requieren experimentación cuantitativa para ser validadas.*

1. **H-DEM-01: Migración de Camino sin Disrupción de Aplicación:**  
   Demostrar que una mutación abrupta de la dirección IP de origen y destino en un flujo UDP activo se asimila en menos de 1 RTT sin pérdida de estado de la aplicación ni re-autenticación.
2. **H-DEM-02: Eficiencia Comparada de Framing frente a HTTP/2 sobre TLS:**  
   Demostrar que el envío periódico de 100 lecturas de sensor estructuradas bajo IPVN7 impone un consumo de datos totales en bytes significativamente menor (al menos un 40% menor) que la misma carga útil enviada como JSON sobre HTTP/2 + TLS sobre TCP.
3. **H-DEM-03: Reducción de Ruido de Señalización en Red Local:**  
   Demostrar que el descubrimiento dirigido basado en consultas amortizadas reduce el tráfico de red en reposo en más del 80% en comparación con mDNS/Bonjour en una red con 10 nodos.
4. **H-DEM-04: Robustez ante Inyección y Corrupción (Tampering Immunity):**  
   Demostrar empíricamente que la pila rechaza y descarta de forma silente el 100% de los paquetes manipulados bit a bit (modificación de encabezado, payload o tag) sin sufrir fugas de memoria, crashes o estados zombi.
5. **H-DEM-05: Coexistencia y Transparencia en Middleboxes Reales:**  
   Demostrar que datagramas IPVN7 encapsulados en UDP estándar atraviesan sin alteración ni descarte routers y puntos de acceso comerciales domésticos estándar.

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
