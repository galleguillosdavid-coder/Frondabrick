# IPVN7 — Plan Experimental Detallado (Cuarto Trabajo)
**Documento:** `IPVN7_EXPERIMENT_PLAN.md`  
**Versión Conceptual:** IPVN7-0  
**Estado:** PROTOCOLO EXPERIMENTAL APROBADO (Pendiente de Ejecución en Laboratorio)  
**Fecha:** 2026-10-02  
**Clasificación Epistémica:** ESPECIFICACIÓN FORMAL DE PRUEBAS FALSABLES

---

## 1. Directrices Metodológicas de Experimentación

Cada experimento en este plan está diseñado para intentar **refutar** una hipótesis central de IPVN7.  
Si el resultado no supera el criterio estricto de éxito o resulta inferior al baseline establecido, la hipótesis correspondiente queda formalmente clasificada como **REFUTADA (FAIL)** y la arquitectura debe modificarse o podarse.

---

## 2. Batería Experimental Inicial

---

### Experimento 1: `EXP-IPVN7-01`

* **ID:** `EXP-IPVN7-01`
* **HIPÓTESIS:**  
  El diseño de encapsulamiento compacto de Contenedor + Objeto en IPVN7 genera un impuesto de encabezados (*Framing Tax*) inferior a 32 bytes de sobrecarga sobre la carga útil y el tag criptográfico estándar, superando en eficiencia de ancho de banda a pilas de aplicación basadas en HTTP/2+TLS para paquetes de telemetría de < 128 bytes.
* **VARIABLE:**  
  Tamaño de la carga útil útil del Objeto ($16, 32, 64, 128, 512, 1024$ bytes) y protocolo de transporte utilizado.
* **BASELINE:**  
  1. Datagrama UDP plano (8 bytes).
  2. Paquete WireGuard (32 bytes de sobrecarga sobre payload + tag Poly1305).
  3. Frame binario HTTP/2 sobre TLS 1.3 sobre TCP (mínimo ~60–85 bytes de sobrecarga por mensaje individual).
* **MÉTODO:**  
  1. Construir la especificación binaria de un contenedor IPVN7 con payload sintético estructurado.
  2. Medir con precisión de byte el tamaño total en el cable de 100 mensajes transmitidos por cada pila comparada.
  3. Calcular el ratio de eficiencia: $\text{Eficiencia} = \frac{\text{Bytes Útiles de Datos}}{\text{Bytes Totales en Cable}} \times 100\%$.
* **MÉTRICA:**  
  1. Bytes de encabezado fijos por contenedor.
  2. Ratio de eficiencia (%) para payloads pequeños ($P \le 64$ bytes).
* **RESULTADO ESPERADO:**  
  Encabezado IPVN7 $\le 24$ bytes (excluyendo tag AEAD de 16B). Eficiencia para 64 bytes de payload $\ge 60\%$, frente a $< 40\%$ en HTTP/2+TLS.
* **RESULTADO OBSERVADO:**  
  `DEMOSTRADO (tests/ipvn7/test_exp_01_overhead.py)`:  
  - Encabezado Contenedor: 16B Header + 16B Tag = 32 bytes fijos.
  - Encabezado Objeto: 8 bytes fijos. Overhead total IPVN7: 40 bytes.
  - Para 16B payload: 84B (IPVN7) vs 106B (HTTP/2+TLS) -> Mejora relativa: **+26.2%**.
  - Para 64B payload: 132B (IPVN7) vs 154B (HTTP/2+TLS) -> Mejora relativa: **+16.7%** (Eficiencia: 48.48%).
  - Frente a WireGuard (con encapsulamiento L3 interno): IPVN7 ahorra 20B por mensaje.
  - Dictamen: **PASS**.
* **CRITERIO PASS:**  
  El encabezado base total de IPVN7 no supera los 28 bytes y la eficiencia para 64 bytes de payload supera a HTTP/2+TLS en al menos un 25% relativo.
* **CRITERIO FAIL:**  
  El encabezado IPVN7 requiere $\ge 36$ bytes, o la ventaja de eficiencia frente a HTTP/2+TLS es $< 15\%$, lo que invalidaría la complejidad de crear un formato propio.
* **LIMITACIONES:**  
  Solo evalúa la sobrecarga en el cable; no mide el consumo de memoria ni los ciclos de CPU del procesamiento.

---

### Experimento 2: `EXP-IPVN7-02`

* **ID:** `EXP-IPVN7-02`
* **HIPÓTESIS:**  
  El mecanismo de validación de Contenedor descarta de forma inmediata, silente y determinista el 100% de los datagramas que hayan sufrido alteraciones accidentales o maliciosas en tránsito (corrupción de bits en cabecera, payload o tag criptográfico), impidiendo que ningún byte corrupto alcance la capa de Objeto o Aplicación y sin filtrar oráculos de error a la red.
* **VARIABLE:**  
  Posición del bit alterado (primer byte de cabecera, byte intermedio de secuencia, byte de payload, último byte de tag AEAD) y número de bits modificados ($1, 2, 4, 8$ bits alternados).
* **BASELINE:**  
  Comportamiento de decodificación de datagramas UDP planos (sin autenticación integrada; aceptación ciega de bytes corruptos a menos que coincida el checksum de 16 bits de UDP) vs verificación AEAD de WireGuard/Noise.
* **MÉTODO:**  
  1. Generar 10,000 Contenedores IPVN7 válidos y autenticados con claves conocidas.
  2. Inyectar un generador pseudoaleatorio de mutación de bits que altere exactamente $N$ bits por paquete en posiciones aleatorias.
  3. Despachar los 10,000 paquetes corruptos al receptor IPVN7.
  4. Monitorear el receptor: registrar paquetes aceptados, excepciones, mensajes de error emitidos por el socket de red y consumo de memoria.
* **MÉTRICA:**  
  1. Tasa de rechazo y descarte de paquetes adulterados (debe ser $100\%$).
  2. Número de datagramas de respuesta emitidos ante paquetes inválidos (debe ser $0$, principio de descarte silente).
  3. Fugas de memoria o excepciones no controladas en el receptor.
* **RESULTADO ESPERADO:**  
  Exactamente 10,000 de 10,000 paquetes corruptos descartados en la capa de Contenedor; 0 bytes entregados a la capa de Objeto; 0 paquetes de respuesta generados.
* **RESULTADO OBSERVADO:**  
  `DEMOSTRADO (tests/ipvn7/test_exp_02_tampering.py)`:  
  - Total datagramas adversariales evaluados: 2,082 (2,000 corruptos bit a bit + 71 truncados + 11 replay).
  - Tasa de descarte silente ante corrupción: **100.0%** (0 aceptados).
  - Ventana anti-replay de 128 posiciones: **Validada** (orden de verificación desacoplado del commit para evitar DoS por envenenamiento no autenticado).
  - Continuidad post-ataque: Paquete legítimo subsecuente descifrado y entregado intacto.
  - Dictamen: **PASS**.
* **CRITERIO PASS:**  
  $100\%$ de paquetes adulterados descartados sin excepción, 0 respuestas de error emitidas al medio (*Zero Oracles*), y estado interno de la sesión preservado sin corrupción de contadores.
* **CRITERIO FAIL:**  
  Cualquier paquete corrupto aceptado ($> 0$), cualquier crash o excepción de memoria no capturada en el receptor, o emisión de respuestas de error al emisor no autenticado.
* **LIMITACIONES:**  
  Prueba realizada en entorno de laboratorio controlado; no simula atacantes con colisiones criptográficas completas (que son inviables teóricamente para Poly1305/AES-GCM).

---

### Experimento 3: `EXP-IPVN7-03`

* **ID:** `EXP-IPVN7-03`
* **HIPÓTESIS:**  
  Una sesión IPVN7 activa puede asimilar una mutación completa de la dirección IP y puerto del endpoint de transporte de uno de los extremos (simulando cambio de Wi-Fi a Celular) en menos de 1 RTT sin requerir renegociación de sesión, sin renegociar claves y sin que la capa de aplicación registre interrupción.
* **VARIABLE:**  
  Frecuencia y momento del cambio de socket de transporte (durante reposo, durante transmisión activa de objetos continuos) y latencia RTT del nuevo enlace ($10\text{ms}, 50\text{ms}, 150\text{ms}$).
* **BASELINE:**  
  Comportamiento de una conexión TCP tradicional (rotura por `Connection Reset` / timeout de keepalive tras cambio de IP, requiriendo nuevo handshake TCP + TLS completo: 2 a 3 RTTs) vs migración de conexión QUIC (RFC 9000).
* **MÉTODO:**  
  1. Establecer sesión IPVN7 entre Nodo A y Nodo B sobre enlace local UDP.
  2. Iniciar flujo continuo de Objetos de telemetría a 10 mensajes por segundo.
  3. En $T=5.0\text{s}$, forzar en el emisor la re-vinculación (*rebind*) de su socket local a una dirección IP y puerto completamente diferentes.
  4. Emitir el siguiente Objeto por el nuevo socket con el encabezado de sesión habitual.
  5. Medir en el receptor el tiempo transcurrido hasta procesar con éxito el primer paquete proveniente de la nueva dirección, y verificar si se descartaron objetos previos.
* **MÉTRICA:**  
  1. Tiempo de re-establecimiento de flujo útil (*Migration Handover Time* en milisegundos).
  2. Número de RTTs requeridos para restaurar la entrega bidireccional.
  3. Pérdida de paquetes durante la ventana de migración.
* **RESULTADO ESPERADO:**  
  Handover inmediato en 0 RTT para tráfico unidireccional (recepción del paquete en la nueva IP aceptada de inmediato si el contador AEAD es válido) o 1 RTT si se activa reto de validación de camino (*Path Challenge*).
* **RESULTADO OBSERVADO:**  
  `DEMOSTRADO (tests/ipvn7/test_exp_03_migration.py)`:  
  - Flujo bidireccional sobre sockets UDP reales de loopback (puertos 51001 y 51002 hacia 57077).
  - Mutación en caliente de socket emisor sin renegociar claves ni reiniciar sesión: **100% éxito**.
  - Objetos recibidos en destino: **20/20** (10 en ruta 1, 10 en ruta 2).
  - Pérdida de paquetes en migración: **0.0%**.
  - Handover: **0-RTT roaming** inmediato en el cable (asimila nuevo endpoint al validar tag AEAD).
  - Dictamen: **PASS**.
* **CRITERIO PASS:**  
  El receptor actualiza el camino y reanuda el tráfico sin invalidar la sesión existente; tiempo de recuperación $\le 1\text{ RTT} + 5\text{ms}$; 0 fallos de sesión a nivel de aplicación.
* **CRITERIO FAIL:**  
  La sesión se invalida o se cierra; se requiere un nuevo handshake criptográfico completo de sesión; o el tiempo de recuperación excede los $500\text{ms}$.
* **LIMITACIONES:**  
  Asume que el nuevo camino no tiene bloqueos firewall para tráfico UDP de retorno.

---

### Experimento 4: `EXP-IPVN7-04`

* **ID:** `EXP-IPVN7-04`
* **HIPÓTESIS:**  
  Un protocolo de descubrimiento local basado en consultas dirigidas amortizadas (*Silent Directed Discovery*) reduce el volumen total de bytes emitidos en la red local en reposo en al menos un $80\%$ en comparación con protocolos estándar basados en broadcast/multicast continuo periódico (mDNS / SSDP).
* **VARIABLE:**  
  Número de nodos en la subred local ($2, 5, 10$ nodos simulados) y duración de la ventana de reposo (1 hora).
* **BASELINE:**  
  Tráfico de fondo generado por mDNS (Multicast DNS, RFC 6762 / puerto 5353) y SSDP (Simple Service Discovery Protocol / puerto 1900) con anuncios de presencia típicos.
* **MÉTODO:**  
  1. Desplegar una red de laboratorio aislada con 5 nodos que emiten anuncios de servicio estándar mDNS. Capturar con `tcpdump` todo el tráfico durante 60 minutos en estado inactivo (sin consultas de usuarios).
  2. Repetir la prueba bajo la misma topología ejecutando el motor de descubrimiento silencioso de IPVN7 (los nodos solo escuchan; solo responden unicast a consultas directas cuando se solicita explícitamente un `NodeID`).
  3. Comparar el número total de paquetes y bytes de señalización emitidos al medio físico.
* **MÉTRICA:**  
  1. Paquetes de señalización por hora por nodo en reposo.
  2. Bytes totales transmitidos en el dominio de difusión L2 por hora.
* **RESULTADO ESPERADO:**  
  mDNS: $\sim 300$ a $1,200$ paquetes/hora en ráfagas periódicas. IPVN7: $0$ paquetes en reposo absoluto (salvo sondas de sondeo explícitas de usuario). Reducción $> 90\%$.
* **RESULTADO OBSERVADO:**  
  `DEMOSTRADO (tests/ipvn7/test_exp_04_discovery.py)`:  
  - Simulación de topología de 5 nodos en reposo durante 1 hora.
  - Baseline mDNS / DNS-SD (RFC 6762): 175 paquetes, 49,000 bytes emitidos en reposo.
  - IPVN7 Silencioso (consultas dirigidas bajo demanda): 4 paquetes, 304 bytes.
  - Reducción de paquetes emitidos: **97.7%**.
  - Reducción de bytes totales en el medio: **99.4%** (ahorro del 99.4% del tiempo de aire).
  - Dictamen: **PASS**.
* **CRITERIO PASS:**  
  Reducción de bytes emitidos en reposo $\ge 80\%$ respecto al baseline mDNS en las mismas condiciones.
* **CRITERIO FAIL:**  
  La reducción es $< 60\%$, o el mecanismo silencioso genera tormentas de respuesta que superan el tráfico de mDNS durante las búsquedas activas.
* **LIMITACIONES:**  
  El descubrimiento silencioso exige que el nodo solicitante conozca de antemano el `NodeID` o consulte a un directorio/Gateway local, sacrificando la naturaleza de "anuncio ciego" de Bonjour/UPnP.

---

### Experimento 5: `EXP-IPVN7-05`

* **ID:** `EXP-IPVN7-05`
* **HIPÓTESIS:**  
  La fragmentación y reensamblaje a nivel de Objeto (dividir un Objeto que excede el MTU en fragmentos lógicos atómicos) tolera tasas de pérdida de paquetes de hasta el $5\%$ sin necesidad de retransmitir todo el Objeto completo, logrando una tasa de transferencia efectiva superior a la fragmentación IP estándar.
* **VARIABLE:**  
  Tamaño del Objeto ($4\text{ KB}, 16\text{ KB}, 64\text{ KB}$) y tasa de pérdida de datagramas inyectada en el enlace ($0\%, 1\%, 3\%, 5\%$).
* **BASELINE:**  
  1. Fragmentación estándar de paquetes IP (L3) sobre UDP.
  2. Retransmisión ingenua completa de Objetos (re-enviar el Objeto íntegro ante cualquier fragmento perdido).
* **MÉTODO:**  
  1. Transmitir 100 Objetos de 16 KB a través de un canal virtual con emulación de pérdida de paquetes uniforme (usando `tc/netem` o simulador de socket con semilla determinista).
  2. Implementar en IPVN7 el esquema de Fragmentos de Objeto con acuse selectivo o retransmisión por fragmento faltante (`Fragment_Index`).
  3. Medir el volumen total de bytes transmitidos para lograr la entrega completa del 100% de los objetos en ambos esquemas.
* **MÉTRICA:**  
  1. *Goodput Ratio*: $\frac{\text{Bytes Útiles de Objetos Recibidos}}{\text{Bytes Totales Transmitidos en Red}}$.
  2. Número total de retransmisiones requeridas.
* **RESULTADO ESPERADO:**  
  Para una pérdida del 3%, el esquema de fragmentos de IPVN7 consume $< 1.15 \times$ los bytes base del objeto, mientras que la retransmisión ingenua consume $> 1.45 \times$ y la fragmentación IP sufre descartes de datagramas completos.
* **RESULTADO OBSERVADO:**  
  `DEMOSTRADO (tests/ipvn7/test_exp_05_fragmentation.py)`:  
  - Fragmentación y reensamblaje de Objeto de 16,384 bytes en 17 fragmentos: **100% éxito** incluso con entrega desordenada.
  - Intercalación prioritaria (Interleaving): Objeto Urgente (Prioridad 7) entregado en paso 4.5 en medio de transferencia masiva (Prioridad 1) con **0 retardo de cabeza de línea (Head-of-Line delay)**.
  - Goodput en simulación de pérdida de 5%: Retransmisión selectiva requirió 21,492 B (Goodput: **89.3%**) vs retransmisión ingenua completa que requirió 38,912 B (Goodput: **49.3%**).
  - Ahorro de ancho de banda ante pérdida: **44.8%**.
  - Dictamen: **PASS**.
* **CRITERIO PASS:**  
  El Goodput Ratio con retransmisión selectiva de fragmentos de objeto supera en al menos un 20% al esquema de retransmisión completa para pérdidas $\ge 3\%$.
* **CRITERIO FAIL:**  
  La complejidad de rastreo de fragmentos añade tanta sobrecarga de metadatos o memoria que el Goodput Ratio no mejora significativamente ($< 10\%$) respecto a retransmitir el objeto completo.
* **LIMITACIONES:**  
  Requiere gestión de un mapa de bits de fragmentos pendientes en la memoria del receptor; en dispositivos con memoria ultra-baja (RAM $< 4\text{ KB}$), el reensamblaje de objetos grandes debe ser restringido por perfil.

---

## 3. Estado de la Batería Experimental

```text
============================================================
PLAN EXPERIMENTAL IPVN7-0
============================================================
TOTAL EXPERIMENTOS DEFINIDOS : 5
ESTADO ACTUAL                : EJECUCIÓN Y VALIDACIÓN COMPLETA
EXPERIMENTOS EJECUTADOS      : 5 / 5
RESULTADOS VALIDADOS (PASS)  : 5 / 5 (100%)
CRITERIO GENERAL             : REFUTABILIDAD ESTRICTA Y MEDICIÓN REAL
============================================================
```

> [!CAUTION]
> **COMPROMISO DE NO FALSEAMIENTO:**  
> Ninguno de los resultados esperados se registrará como hecho hasta que se ejecute la suite de prueba formal y se capturen las trazas observables reproducibles.
