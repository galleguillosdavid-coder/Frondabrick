# IPVN7 — AUDITORÍA EPISTÉMICA Y TÉCNICA DE LA BATERÍA INICIAL (IPVN7-0)

**Documento:** `IPVN7_EMPIRICAL_AUDIT_0.md`  
**Fecha:** 2026-10-02  
**Clasificación Epistémica:** AUDITORÍA TÉCNICA RIGUROSA / RECLASIFICACIÓN  
**Principio Rector:** LA EVIDENCIA MANDA — Cero inflación de claims  

---

## 1. Motivo y Alcance de la Auditoría

En cumplimiento del **Mandato de Autonomía Total Controlada**, se realizó una revisión línea por línea, cálculo por cálculo y supuesto por supuesto de la batería experimental inicial (`EXP-IPVN7-01` a `EXP-IPVN7-05`).

El objetivo es erradicar cualquier sesgo de confirmación, falsa equivalencia en los baselines o generalización indebida de resultados de laboratorio.

---

## 2. Dictamen Detallado por Experimento

---

### Experimento 1: `EXP-IPVN7-01` (Framing Tax / Sobrecarga de Encabezados)

* **Script:** `tests/ipvn7/test_exp_01_overhead.py`
* **Medición Verificada:**
  - Encabezado Contenedor: 16 bytes fijos.
  - Tag AEAD Poly1305: 16 bytes fijos.
  - Encabezado de Objeto: 8 bytes fijos.
  - Sobrecarga total de encapsulado IPVN7: **40 bytes por mensaje individual**.
* **Auditoría de Baselines y Equivalencia Semántica:**
  1. *Frente a WireGuard (túnel VPN L3):*  
     El baseline del test (`20 + 8 + 16 + 20 + 8 + payload + 16 = 88 + payload`) modela con precisión una aplicación que envía datagramas UDP a través de un túnel VPN WireGuard tradicional. En ese escenario, IPVN7 ahorra **20 bytes netos** al evitar la duplicación de cabeceras IP y UDP internas.  
     **Matiz Crítico:** Si una aplicación utilizara la biblioteca Noise Protocol directamente sobre UDP para transportar datos de aplicación (sin túnel de red del kernel), Noise requeriría únicamente 8B de secuencia + 16B de tag = 24 bytes, siendo 16 bytes más compacto que IPVN7. IPVN7 paga 16B adicionales a cambio de: Magic/Version (2B), Reserved/Flags (2B), Receiver Index (4B) y el encabezado de Objeto tipado (8B).
  2. *Frente a HTTP/2 + TLS 1.3 sobre TCP:*  
     El cálculo de 90 bytes fijos modela adecuadamente un frame `DATA` acompañado de un frame `HEADERS` comprimido con HPACK en régimen estacionario.
* **Clasificación Epistémica:**
  $$\boxed{\text{DEMOSTRADO}}$$
  *Dentro del alcance definido: la sobrecarga de 40B es exacta y medible en el cable para encapsulado directo de objetos autenticados.*

---

### Experimento 2: `EXP-IPVN7-02` (Inmutabilidad y Descarte Silente)

* **Script:** `tests/ipvn7/test_exp_02_tampering.py`
* **Medición Verificada:**
  - 2,000 datagramas con mutación de bits aleatoria (1, 2, 4 y 8 bits alterados en cabecera AAD, texto cifrado y tag Poly1305).
  - Tasa de rechazo: **100.0% silente** (0 excepciones no controladas, 0 oráculos de error devueltos).
  - 71 variantes truncadas rechazadas al 100%.
  - Resistencia a replay verificada con ventana deslizante de 128 posiciones.
* **Auditoría de Vulnerabilidad Resuelta:**
  - La verificación separada `can_accept` (pre-autenticación, sólo lectura) y `commit` (post-autenticación) previene el ataque de denegación de servicio por envenenamiento de secuencia (*Sequence Poisoning DoS*).
* **Límite Detectado:**
  - ChaCha20-Poly1305 utiliza un contador de 64 bits para el Nonce. Si una sesión prolongada transmitiera $2^{64}$ paquetes sin re-clavear (*rekeying*), se produciría una reutilización catastrófica de Nonce. La arquitectura DEBE especificar formalmente un límite estricto de re-claveo periódico (ej. cada $2^{32}$ paquetes o cada 2 horas).
* **Clasificación Epistémica:**
  $$\boxed{\text{DEMOSTRADO}}$$
  *Propiedad de integridad, autenticidad y descarte silente verificada experimentalmente.*

---

### Experimento 3: `EXP-IPVN7-03` (Migración de Camino / Roaming)

* **Script:** `tests/ipvn7/test_exp_03_migration.py`
* **Auditoría Crítica de Metodología:**
  - El ensayo probó el cambio de socket emisor entre dos puertos UDP locales en la misma interfaz de loopback:
    $$127.0.0.1:51001 \longrightarrow 127.0.0.1:51002 \quad \text{hacia} \quad 127.0.0.1:57077$$
  - **Reclamo Anterior Excesivo:** Llamar a esto "Roaming de Red Demostrado" es metodológicamente incorrecto. No involucra interfaces físicas distintas, subredes IP distintas, variación de MTU, ni atravesamiento de NAT simétrico.
* **Vulnerabilidad de Seguridad Identificada (*Unauthenticated Endpoint Hijacking / Reflection*):**
  - Si un nodo receptor actualiza inmediatamente la dirección de destino a la que enviará respuestas basándose únicamente en la dirección origen del último paquete AEAD recibido, un atacante que pueda observar el tráfico o reflejar tráfico en redes locales podría provocar que el servidor envíe tráfico a un tercero inocente (Ataque de Reflexión/Amplificación).
  - Estándares maduros como QUIC (RFC 9000, Sección 9) exigen **Path Validation** mediante el intercambio de un reto criptográfico (`PATH_CHALLENGE` / `PATH_RESPONSE`) antes de emitir tráfico a una nueva dirección IP no validada.
* **Clasificación Epistémica:**
  $$\boxed{\text{PARCIALMENTE DEMOSTRADO}}$$
  *Demostrado únicamente: desacoplamiento de la 4-tupla en la capa de descifrado UDP local. NO demostrado: roaming multi-interfaz ni resistencia a ataques de reflexión sin Path Validation.*

---

### Experimento 4: `EXP-IPVN7-04` (Tráfico en Reposo / Descubrimiento)

* **Script:** `tests/ipvn7/test_exp_04_discovery.py`
* **Auditoría Crítica de Metodología:**
  - El script utilizó una clase simulada `IPVN7SilentNode` cuyo método `simulate_hour_idle` ejecuta literalmente la instrucción `pass`.
  - **Falsa Equivalencia Experimental:** Comparar una tasa analítica teórica de mDNS contra un bucle Python que no ejecuta operaciones de red no constituye una medición física ni experimental de red. Es una tautología analítica ("un nodo programado para no emitir, emite 0 bytes").
  - **Omisión del Costo de Bootstrap:** Si ningún nodo anuncia su presencia, un nodo emisor no puede comunicarse con un nodo destino a menos que:
    1. Conozca su IP y clave previamente (*Out-of-band* o archivo de configuración estático).
    2. Emita una sonda de sondeo (*Discovery Probe*) por broadcast/multicast en el momento en que desea comunicarse. En este último caso, la red no es pasiva, sino que intercambia tráfico periódico por ráfagas de sondeo bajo demanda.
* **Clasificación Epistémica:**
  $$\boxed{\text{INFERENCIA / MODELO TEÓRICO}}$$
  *Reclasificado de DEMOSTRADO a MODELO TEÓRICO. Requiere implementación en sockets reales con medición de sondas bajo demanda y resolución de nombres para ser considerado empírico.*

---

### Experimento 5: `EXP-IPVN7-05` (Fragmentación e Intercalación)

* **Script:** `tests/ipvn7/test_exp_05_fragmentation.py`
* **Medición Verificada:**
  - Reensamblaje atómico de un payload de 16,384 bytes en 17 fragmentos, tolerando desorden total.
  - La intercalación lógica de un objeto de prioridad 7 en el buffer del reensamblador se entrega de inmediato (paso 4.5) sin esperar a los fragmentos restantes del objeto de prioridad 1.
  - La retransmisión selectiva ante 5% de pérdida ahorra 44.8% de bytes en comparación con retransmitir el objeto completo.
* **Matiz Crítico de Red Real:**
  - El experimento demostró la ausencia de Head-of-Line Blocking a nivel del **reensamblador de aplicación**.
  - **Sin embargo**, en un enlace de red real con congestión o colas en el socket del sistema operativo (`SO_SNDBUF`), si el emisor encola masivamente 100 fragmentos en el buffer del kernel antes de encolar el comando urgente, el paquete urgente quedará encolado físicamente en la interfaz de red detrás de los fragmentos a menos que el emisor implemente un **Planificador de Salida con Colas de Prioridad (*Priority Egress Scheduler*)**.
* **Clasificación Epistémica:**
  $$\boxed{\text{PARCIALMENTE DEMOSTRADO}}$$
  *Demostrado: reensamblaje atómico e intercalación en recepción. Pendiente: planificador de salida en el emisor para evitar bloqueo en colas de transmisión.*

---

## 3. Matriz Epistémica Corregida Post-Auditoría

| ID | Reclamo Original | Estado Post-Auditoría | Justificación / Corrección |
| :--- | :--- | :---: | :--- |
| `EXP-01` | Sobrecarga 40B vs baselines | **DEMOSTRADO** | Exacto para app sobre UDP vs VPN L3 y HTTP/2. Se documenta que Noise puro sin objetos tiene 16B menos. |
| `EXP-02` | Integridad y descarte silente | **DEMOSTRADO** | 100% verificado sobre 2,000 mutaciones de bits. Se identifica requisito de re-claveo por agotamiento de nonce. |
| `EXP-03` | Roaming de endpoint | **PARCIALMENTE DEMOSTRADO** | Solo probado en puertos de loopback. Requiere validación de camino (*Path Challenge*) contra ataques de reflexión. |
| `EXP-04` | Red silenciosa en reposo | **INFERENCIA / MODELO TEÓRICO** | La simulación usó `pass`. Debe medirse con sockets reales y evaluar el costo de sondeo bajo demanda. |
| `EXP-05` | Intercalación anti-HoL | **PARCIALMENTE DEMOSTRADO** | Probado en reensamblador lógico. Requiere planificador de colas de salida en el emisor. |

---

## 4. Progresión Autónoma Ejecutada y Cadencia Operativa

### Fases Completadas y Demostradas:
1. **`EXP-IPVN7-06` (Apretón de Manos Criptográfico Noise_IK en 1-RTT):** Demostrado (116B Init, 60B Resp, 100% rechazo adversarial, PFS).
2. **`EXP-IPVN7-07` (Validación de Camino contra Reflexión - Path Challenge):** Demostrado (40B Challenge/Response, factor de amplificación 0.48x, anti-secuestro).
3. **`EXP-IPVN7-08` (Planificador de Salida con Colas de Prioridad - Egress Anti-HoL):** Demostrado (-98.9% latencia urgente, 100% integridad masiva).

### Mandato Operativo de Cadencia (/schedule):
> **REGLA DE PROGRESIÓN OBLIGATORIA:**  
> Al finalizar cada ciclo autónomo de investigación/experimento, se programa inmediatamente un temporizador `/schedule` para ejecución en **10 minutos (600 segundos)** con el siguiente paso autónomo especificado (`EXP-IPVN7-09: Re-claveo Transparente en Vuelo`). El proyecto avanza de forma continua y autónoma mientras existan brechas técnicas demostrables.

