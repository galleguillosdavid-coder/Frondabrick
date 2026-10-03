# IPVN7 — Revisión Crítica Arquitectónica (Segundo Trabajo)
**Documento:** `IPVN7_CRITICAL_REVIEW.md`  
**Versión Conceptual:** IPVN7-0  
**Estado:** REVISIÓN CRÍTICA PRE-IMPLEMENTACIÓN (Anti-Complejidad / Navaja de Ockham)  
**Fecha:** 2026-10-02  
**Clasificación Epistémica:** EVALUACIÓN CRÍTICA Y REFUTACIÓN TEMPRANA

---

## 1. Propósito de la Revisión Crítica

En cumplimiento de la regla:
> *"Si una capa no aporta valor: ELIMINARLA. Si una abstracción agrega complejidad sin beneficio: ELIMINARLA."*

Esta revisión somete cada componente propuesto en la línea base a 7 preguntas obligatorias:
1. **¿Es necesario?**
2. **¿Existe ya?**
3. **¿Podemos reutilizarlo?**
4. **¿Qué problema resuelve?**
5. **¿Qué complejidad agrega?**
6. **¿Cómo se prueba?**
7. **¿Cómo puede fallar?**

---

## 2. Análisis Crítico por Componente

---

### Componente 1: `CHANNEL` (Canales Lógicos Multiplexados)

* **¿Es necesario?**  
  **DUDOSO / CUESTIONABLE.** Es la abstracción más vulnerable a sobreingeniería en la arquitectura inicial. Si una sesión transporta Objetos discretos con un campo de prioridad o tipo, la necesidad de mantener máquinas de estado independientes para "canales" dentro de la misma sesión puede ser redundante.
* **¿Existe ya?**  
  **SÍ.** Existe en SCTP (streams), HTTP/2 y QUIC (streams bidireccionales y unidireccionales), SSH (channels multiplexados), BEEP (RFC 3080).
* **¿Podemos reutilizarlo?**  
  **SÍ.** Si se adopta QUIC como transporte subyacente, QUIC ya resuelve la multiplexación de streams sin bloqueo de cabeza de línea (*Head-of-Line Blocking*). Reimplementar canales lógicos propios sobre UDP obligaría a crear un planificador de congestión y control de flujo por canal (*stream-level flow control*), una de las partes más complejas y propensas a errores de QUIC/SCTP.
* **¿Qué problema resuelve?**  
  Evita que la transferencia masiva de un archivo monopolice el enlace e impida la llegada oportuna de comandos de control o mensajes de texto.
* **¿Qué complejidad agrega?**  
  **ALTA.** Requiere contabilidad de créditos de ventana por canal, buffers separados por canal, priorización (round-robin ponderado o colas estrictas) y gestión de estados de apertura/cierre por canal.
* **¿Cómo se prueba?**  
  Inyectar saturación masiva de datos en Canal A y medir si la latencia de entrega de un Objeto crítico en Canal B se mantiene por debajo de un umbral temporal establecido.
* **¿Cómo puede fallar?**  
  Inanición (*starvation*) de canales de baja prioridad; desbordamiento de memoria por buffering en canales bloqueados; bugs sutiles en la sincronización de estados.
* **Veredicto Arquitectónico Preliminar:**  
  > [!WARNING]
  > **Recomendación:** **SIMPLIFICAR O APLAZAR.** Para el prototipo inicial, no implementar canales con máquinas de estado completas. Utilizar simplemente un campo de 3 bits de prioridad (*Priority Class*) y un identificador de flujo (*Stream/Flow ID*) en el encabezado del Objeto, delegando el scheduling grueso al transporte o a una cola simple.

---

### Componente 2: `SESSION` (Contexto Criptográfico e Identidad Lógica)

* **¿Es necesario?**  
  **ABSOLUTAMENTE SÍ.** Es el corazón del desacoplamiento. Sin una sesión desacoplada de la dirección IP/puerto, el protocolo colapsa de inmediato al modelo de socket tradicional de Berkeley.
* **¿Existe ya?**  
  **SÍ.** Noise Protocol Framework (Handshake state + CipherState), WireGuard sessions, TLS 1.3 resumption, IPsec IKEv2 Security Associations (SA), QUIC Connection ID / Session.
* **¿Podemos reutilizarlo?**  
  **SÍ.** No diseñar protocolo de apretón de manos propio. Reutilizar **Noise Protocol Framework (Noise_IK o Noise_XX)** proporciona garantías formales de autenticación mutua, confidencialidad, integridad y derivación de claves probadas matemáticamente.
* **¿Qué problema resuelve?**  
  Permite que dos nodos mantengan un acuerdo criptográfico de confianza mutua que sobrevive a cambios de dirección física, reinicios de interfaz de red y traversal de NAT intermediarios.
* **¿Qué complejidad agrega?**  
  **MEDIA.** Máquina de estados criptográfica (handshake, rotación de claves, timers de keepalive y expiración).
* **¿Cómo se prueba?**  
  Establecer sesión, alterar la IP origen/destino del socket emisor, enviar datagrama y verificar que el receptor lo descifra y acepta sin re-autenticación.
* **¿Cómo puede fallar?**  
  Desincronización de números de secuencia; consumo de memoria por inundación de handshakes incompletos (ataque de agotamiento de estado); expiración no detectada de claves.
* **Veredicto Arquitectónico Preliminar:**  
  > [!TIP]
  > **Recomendación:** **MANTENER COMO PILAR CENTRAL.** Reutilizar Noise Framework directamente para evitar inventar criptografía.

---

### Componente 3: `CONTAINER` (Unidad Atómica de Transporte y Framing)

* **¿Es necesario?**  
  **ABSOLUTAMENTE SÍ.** La red física procesa datagramas discretos. Se requiere una delimitación exacta de bytes que contenga el tag de autenticación (AEAD), el número de secuencia anti-replay y la demarcación del payload.
* **¿Existe ya?**  
  **SÍ.** Datagrama WireGuard (Type, Receiver Index, Counter, Encrypted Payload), QUIC Packet, ESP packet en IPsec.
* **¿Podemos reutilizarlo?**  
  **PARCIALMENTE.** Podemos inspirarnos en el framing compacto y de tamaño fijo de WireGuard, pero adaptado para encapsular Objetos tipificados de IPVN7.
* **¿Qué problema resuelve?**  
  Protege la confidencialidad e integridad del tráfico en tránsito; provee detección inmediata de tampering y descarte temprano de paquetes corruptos o repetidos antes de tocar el espacio de usuario.
* **¿Qué complejidad agrega?**  
  **BAJA a MEDIA.** Serialización/deserialización binaria estructurada; cálculo de AEAD (Poly1305 / GCM); verificación de ventana de replay mediante un bitmask de 64 o 128 bits.
* **¿Cómo se prueba?**  
  Generar contenedores, alterar 1 bit en cualquier posición del paquete y verificar que el receptor descarta el 100% de los contenedores adulterados sin emitir respuesta.
* **¿Cómo puede fallar?**  
  Desbordamiento de tamaño frente al MTU de la ruta (fragmentación forzada L3); overhead porcentualmente excesivo en datagramas ultrapequeños.
* **Veredicto Arquitectónico Preliminar:**  
  > [!TIP]
  > **Recomendación:** **MANTENER.** Debe diseñarse con obsesión por el minimalismo (máximo 16 a 24 bytes de encabezado base excluyendo el tag AEAD).

---

### Componente 4: `OBJECT` (Unidad Lógica de Datos Estructurada)

* **¿Es necesario?**  
  **SÍ, CONDICIONADO A SU SIMPLICIDAD.** Si la red solo mueve bytes planos (*bytestream*), la aplicación vuelve a tener que diseñar delimitación (framing de aplicación). Si el Objeto es atómico (longitud explícita + tipo + ID de correlación), la aplicación se simplifica radicalmente.
* **¿Existe ya?**  
  **SÍ.** CBOR (RFC 8949), Protocol Buffers, ASN.1, CoAP Messages (RFC 7252), MQTT Packets.
* **¿Podemos reutilizarlo?**  
  **SÍ.** No inventar un serializador propio. Se puede definir el contenedor con un formato TLV (Type-Length-Value) ultra-compacto o basar la codificación de objetos en **CBOR canónico** o TLV binario plano de longitud fija/varint.
* **¿Qué problema resuelve?**  
  Permite que el núcleo de la red agrupe, priorice y descarte información de manera coherente (ej. descartar un frame de telemetría expirado en favor de un objeto de comando).
* **¿Qué complejidad agrega?**  
  **MEDIA.** Parsing de tipos, manejo de límites de tamaño, reensamblaje si un objeto excede el tamaño máximo de un contenedor.
* **¿Cómo se prueba?**  
  Enviar objetos heterogéneos (un string corto, un bloque binario de 64KB fragmentado, un comando escalar) y verificar entrega intacta y deserialización exacta.
* **¿Cómo puede fallar?**  
  Ataques de parsing (longitudes declaradas que exceden el buffer real, campos anidados que provocan desbordamiento de pila); penalización de CPU si la serialización es compleja.
* **Veredicto Arquitectónico Preliminar:**  
  > [!TIP]
  > **Recomendación:** **MANTENER EN FORMATO TLV PLANO.** Un encabezado de objeto de no más de 4 a 8 bytes: `[Type: 1B][Flags: 1B][Length: 2B][Object_ID: 4B]`. Sin esquemas complejos en tiempo de ejecución.

---

### Componente 5: `PATH` (Abstracción de Camino y Movilidad)

* **¿Es necesario?**  
  **SÍ.** Es el mecanismo que hace operativo el desacoplamiento entre sesión y red física.
* **¿Existe ya?**  
  **SÍ.** QUIC Connection Migration (RFC 9000 Sec 9), WireGuard Cryptokey Routing (roaming pasivo por endpoint learning), Multipath TCP (MPTCP RFC 8684), SCTP multihoming.
* **¿Podemos reutilizarlo?**  
  **SÍ.** El mecanismo de WireGuard (actualizar el endpoint remoto al recibir un paquete válido con clave y contador mayor) es el más elegante, rápido y probado para caminos únicos móviles. Para multipath activo (enviar por dos caminos a la vez), el modelo de MPTCP o QUIC multipath ofrece el diseño de referencia.
* **¿Qué problema resuelve?**  
  Permite cambiar de red (Wi-Fi $\to$ Celular $\to$ Ethernet) sin interrumpir la sesión ni requerir que el usuario vuelva a iniciar sesión.
* **¿Qué complejidad agrega?**  
  **MEDIA a ALTA.** Medición de RTT por camino, sondas de validación de camino (*path probing*) para evitar amplificación y secuestro de ruta, manejo de pérdida de conectividad temporal.
* **¿Cómo se prueba?**  
  Establecer tráfico continuo, cambiar la IP local mediante enlace secundario, y medir tiempo de reconexión y paquetes perdidos.
* **¿Cómo puede fallar?**  
  Vulnerabilidad a secuestro de tráfico si un paquete falsificado engaña al nodo para cambiar el camino; saturación por multipath mal balanceado.
* **Veredicto Arquitectónico Preliminar:**  
  > [!TIP]
  > **Recomendación:** **MANTENER CON MODELO MIGRATORIO PASIVO/VERIFICADO.** Inspirarse en el roaming de WireGuard + verificación de retorno de ruta tipo QUIC PATH_CHALLENGE para evitar ataques de redirección.

---

### Componente 6: `PROFILE` (Conciencia de Capacidades Heterogéneas)

* **¿Es necesario?**  
  **DUDOSO COMO CAPA DE PROTOCOLO; SÍ COMO CONFIGURACIÓN DE IMPLEMENTACIÓN.**  
  Hacer que el cable o los encabezados transporten "perfiles" abstractos suele ser sobreingeniería. Los perfiles son relevantes para cómo el software local asigna buffers, define timers y selecciona suites criptográficas, no necesariamente como una cabecera de red.
* **¿Existe ya?**  
  **SÍ.** Perfiles de Bluetooth (BLE Profiles), perfiles de Zigbee, CoAP options, TLS ClientHello capabilities.
* **¿Podemos reutilizarlo?**  
  **SÍ.** Intercambio de parámetros durante el handshake (ej. tamaño máximo de contenedor aceptado, ventana de recepción, soporte de extensiones).
* **¿Qué problema resuelve?**  
  Evita que un servidor abrume a un sensor pequeño con buffers que no puede alojar o paquetes que no puede procesar.
* **¿Qué complejidad agrega?**  
  **BAJA si es estático / ALTA si es dinámico y negociado continuamente.**
* **¿Cómo se prueba?**  
  Conectar un nodo simulado `PROFILE_SENSOR` con buffer limitado a 2KB a un servidor emitiendo a 10MB/s; comprobar que el servidor modula su envío y no satura al sensor.
* **¿Cómo puede fallar?**  
  Matriz de incompatibilidad combinatoria (perfil X no puede comunicarse con perfil Y por exceso de divergencia en parámetros).
* **Veredicto Arquitectónico Preliminar:**  
  > [!WARNING]
  > **Recomendación:** **ELIMINAR COMO CAPA EN EL CABLE.** Convertir `Profile` en una plantilla de configuración local del motor (`Runtime Configuration`) y reducir su presencia en red a un simple intercambio de parámetros operacionales (*Transport Parameters*) en el handshake inicial.

---

### Componente 7: `DISCOVERY` (Descubrimiento Silencioso)

* **¿Es necesario?**  
  **SÍ, PERO CON ALCANCE ESTRICTO.** Los nodos deben poder encontrarse en una red local sin configuración manual previa en ciertos escenarios.
* **¿Existe ya?**  
  **SÍ.** mDNS/DNS-SD (Bonjour), SSDP (UPnP), WS-Discovery, DHTs (Kademlia en BitTorrent/IPFS), BLE Advertising.
* **¿Podemos reutilizarlo?**  
  **SÍ.** Se puede reutilizar mDNS estándar para entornos LAN de desarrollo, o diseñar un mecanismo unicast/direct-probe sobre UDP si se quiere silenciar el broadcast.
* **¿Qué problema resuelve?**  
  Conexión sin configuración previa (*Zero-Conf*) entre dispositivos cercanos.
* **¿Qué complejidad agrega?**  
  **ALTA.** Temporizadores, cachés de presencia, resolución de colisiones, riesgo de saturación de medio por ráfagas de consultas.
* **¿Cómo se prueba?**  
  Desplegar 10 nodos en una subred, iniciar consultas dirigidas y medir con Wireshark/tcpdump el volumen total de bytes emitidos durante 1 hora en reposo.
* **¿Cómo puede fallar?**  
  Filtros de broadcast/multicast en redes empresariales o Wi-Fi con aislamiento de clientes; tormentas de respuestas si múltiples nodos responden a la vez.
* **Veredicto Arquitectónico Preliminar:**  
  > [!WARNING]
  > **Recomendación:** **AISLAR DEL NÚCLEO.** El descubrimiento debe ser un servicio opcional superior o auxiliar, NO un componente interno del CORE de transporte. El CORE solo necesita saber: *tengo este NodeID y este Endpoint físico*. Cómo se descubrió ese endpoint debe ser agnóstico.

---

### Componente 8: `GATEWAY` (Puerta de Enlace y Relevo)

* **¿Es necesario?**  
  **SÍ EN EL MUNDO REAL.** Sin gateways o relays, la comunicación peer-to-peer falla en > 70% de los entornos residenciales y móviles debido a CGNAT y firewalls simétricos.
* **¿Existe ya?**  
  **SÍ.** STUN (RFC 8489), TURN (RFC 8656), ICE (RFC 8445), Derp servers (Tailscale), Relays de Tor, Libp2p Circuit Relay.
* **¿Podemos reutilizarlo?**  
  **SÍ.** La arquitectura de relay autenticado de Derp (Tailscale) o TURN demuestra que reenviar datagramas cifrados punto a punto basándose en el NodeID de destino sin descifrar el payload es eficiente, seguro y viable.
* **¿Qué problema resuelve?**  
  Conectividad universal a través de redes celulares, NATs empresariales y saltos entre protocolos físicos heterogéneos.
* **¿Qué complejidad agrega?**  
  **MEDIA a ALTA.** Mantener estados de mapeo de relay, balanceo de carga, ancho de banda centralizado consumido por intermediación.
* **¿Cómo se prueba?**  
  Colocar dos nodos tras dos NATs estrictos diferentes sin apertura de puertos e intercambiar objetos a través del Gateway; medir latencia adicional vs camino directo.
* **¿Cómo puede fallar?**  
  Punto único de fallo si no hay redundancia; cuello de botella de ancho de banda; aumento de latencia RTT al triangular por el relay.
* **Veredicto Arquitectónico Preliminar:**  
  > [!TIP]
  > **Recomendación:** **MANTENER COMO ROL DE NODO.** Un Gateway no es un protocolo diferente, es simplemente un Nodo ordinario de IPVN7 que tiene capacidad de enrutar contenedores opacos hacia otros nodos cuando el camino directo no está disponible.

---

## 3. Síntesis Crítica y Poda Arquitectónica (Navaja de Ockham)

Tras el análisis de las 7 preguntas, la pila propuesta inicialmente en `IPVN7_ARCHITECTURE_BASELINE.md` se somete a una poda rigurosa:

### Pila Inicial (9 Capas):
$$\text{App} \to \text{Profile} \to \text{Channel} \to \text{Session} \to \text{Container} \to \text{Object} \to \text{Path} \to \text{Transport} \to \text{Network}$$

### Pila Depurada y Justificada (Minimal Core):
```text
┌────────────────────────────────────────────────────────┐
│                   APLICACIÓN (App)                     │
│               Lógica, intención y datos                │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                     OBJETO (Object)                    │
│      Unidad lógica estructurada [Type, Length, ID]     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    SESIÓN (Session)                    │
│    Identidad mutua (Noise IK/XX), AEAD y Replay Window │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 CONTENEDOR (Container)                 │
│         Framing compacto [Header, Sequence, Tag]       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  CAMINO & TRANSPORTE                   │
│        Path Manager (Roaming/Relay) sobre UDP          │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   RED FÍSICA EXISTENTE                 │
│                      IPv4 / IPv6                       │
└────────────────────────────────────────────────────────┘
```

### Razonamiento de la Poda:
1. **`Profile`:** Eliminado de la cabecera de red. Pasa a ser configuración local de nodo e intercambio de parámetros de transporte en el apretón de manos inicial.
2. **`Channel`:** Degradado de "capa independiente con máquina de estados" a un atributo de metadatos ligero en el encabezado del Objeto (`Priority / Stream ID`). Se evita la duplicación de planificadores de congestión complejos.
3. **`Discovery`:** Extraído del CORE de transporte. El CORE procesa paquetes entre identidades conocidas y endpoints resueltos; el descubrimiento opera como un servicio periférico desacoplado.

---

## 4. Conclusión de la Revisión Crítica

El valor real que justifica la existencia de IPVN7 se concentra en tres elementos irreductibles:
1. **Identidad Criptográfica de Nodo desacoplada de la dirección IP.**
2. **Sesión resiliente que mantiene el contexto de cifrado a través de cambios de red física (Roaming/Movilidad nativa).**
3. **Manejo nativo de Objetos estructurados atómicos sin requerir protocolos de aplicación artesanales por encima.**

Cualquier otra capa agregada en esta fase inicial que no sirva directamente a estos tres objetivos constituye **deuda técnica prematura**.
