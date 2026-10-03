# IPVN7 — Especificación Binaria del Protocolo Mínimo (v0)
**Documento:** `IPVN7_BINARY_SPEC_v0.md`  
**Versión de Protocolo:** IPVN7-v0 (Draft Mínimo de Laboratorio)  
**Fecha:** 2026-10-02  
**Clasificación Epistémica:** ESPECIFICACIÓN DE INGENIERÍA / DRAFT DE IMPLEMENTACIÓN

---

## 1. Principio de Framing Mínimo

El protocolo IPVN7-v0 adopta una arquitectura de framing binario de longitud prefijada con alineación de 64 bits en la medida de lo posible, evitando parsers basados en texto o delimitadores variables.

La encapsulación sigue la estructura:
```text
┌────────────────────────────────────────────────────────┐
│           ENCABEZADO DE TRANSPORTE (UDP - 8 bytes)     │
├────────────────────────────────────────────────────────┤
│          CABECERA DE CONTENEDOR (14 bytes)             │
├────────────────────────────────────────────────────────┤
│          CARGA ÚTIL CIFRADA (1 o más Objetos)          │
│          ┌──────────────────────────────────────────┐  │
│          │  Encabezado de Objeto (8 bytes)          │  │
│          ├──────────────────────────────────────────┤  │
│          │  Payload de Datos del Objeto (N bytes)   │  │
│          └──────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│       ETIQUETA DE AUTENTICACIÓN AEAD (16 bytes)        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Formato del Contenedor (`Container`)

Todo datagrama IPVN7 que viaja sobre UDP contiene una cabecera de Contenedor en texto plano (pero autenticada en los datos asociados del AEAD) y un bloque de carga cifrado.

### Distribución de Bytes del Contenedor (Header: 16 bytes)
```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Magic (0x77) |  Type / Flags |     Reserved (0x0000)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Session Receiver Index (32 bits)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                   Sequence Counter (64 bits)                  +
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     Encrypted Payload ...                     |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  AEAD Auth Tag (128 bits / 16 bytes)          |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Campos del Contenedor:
1. **`Magic` (uint8, 1 byte):** Constante identificadora del protocolo. En v0 se fija en `0x77` (ascii 'w' / 'IPVN7 wire').
2. **`Type / Flags` (uint8, 1 byte):**
   - `0x01`: `DATA` (Datagrama con Objetos cifrados).
   - `0x02`: `HANDSHAKE_INIT` (Apertura de sesión Noise_IK / Noise_XX).
   - `0x03`: `HANDSHAKE_RESP` (Respuesta de sesión Noise).
   - `0x04`: `PATH_CHALLENGE` (Sonda de verificación de nuevo camino).
   - `0x05`: `PATH_RESPONSE` (Respuesta a sonda de camino).
3. **`Reserved` (uint16, 2 bytes):** Reservado para alineación de 32 bits y extensiones futuras (debe emitirse en `0x0000`; receptor debe ignorar en v0).
4. **`Session Receiver Index` (uint32 Little-Endian, 4 bytes):** Índice o identificador local de la sesión en el nodo receptor. Permite resolver la clave de sesión y el estado de descifrado en $O(1)$ sin exponer la clave pública de los participantes.
5. **`Sequence Counter` (uint64 Little-Endian, 8 bytes):** Contador monótono de 64 bits por sesión. Se utiliza como nonce para el cifrador AEAD y para la ventana deslizante anti-replay.
6. **`Encrypted Payload` (Longitud variable):** Carga útil cifrada mediante ChaCha20-Poly1305.
7. **`AEAD Auth Tag` (16 bytes):** Tag de autenticación e integridad Poly1305 calculado sobre los 16 bytes de cabecera de contenedor (como datos asociados adicionales / *AAD*) y el texto cifrado.

> **Sobrecarga fija de Contenedor:** $16 \text{ bytes de cabecera} + 16 \text{ bytes de tag} = \mathbf{32\text{ bytes}}$.

---

## 3. Formato del Objeto (`Object`)

Los objetos viajan **dentro** de la carga cifrada del contenedor. Un solo contenedor puede alojar uno o múltiples objetos consecutivos si el tamaño lo permite.

### Distribución de Bytes del Objeto (Header: 8 bytes)
```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Object Type  | Flags/Priority|      Payload Length (16 bits) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Object / Stream ID (32 bits)                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Object Payload Bytes ...                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Campos del Objeto:
1. **`Object Type` (uint8, 1 byte):**
   - `0x01`: `RAW_BYTES` (Flujo opaco de bytes).
   - `0x02`: `STRUCTURED_TELEMETRY` (Pares clave/valor compactos o CBOR).
   - `0x03`: `TEXT_MESSAGE` (Cadena UTF-8).
   - `0x04`: `FILE_FRAGMENT` (Fragmento indexado de archivo o transferencia masiva).
   - `0x05`: `RPC_COMMAND` (Comando o solicitud de invocación).
   - `0x06`: `RPC_RESPONSE` (Resultado o respuesta a invocación).
2. **`Flags / Priority` (uint8, 1 byte):**
   - Bits `[7:5]` (3 bits): Nivel de prioridad de entrega ($0 = \text{Baja / Fondo}$, $4 = \text{Normal}$, $7 = \text{Urgente / Control}$).
   - Bit `[4]` (1 bit): `FRAG` (El objeto es parte de una secuencia fragmentada).
   - Bit `[3]` (1 bit): `LAST_FRAG` (Último fragmento de un objeto compuesto).
   - Bits `[2:0]` (3 bits): Reservados (emitidos en 0).
3. **`Payload Length` (uint16 Little-Endian, 2 bytes):** Tamaño en bytes de la carga útil del objeto (máximo 65,535 bytes por fragmento individual; acotado habitualmente por el MTU del contenedor).
4. **`Object / Stream ID` (uint32 Little-Endian, 4 bytes):** Identificador unívoco del objeto o flujo para reensamblaje y deduplicación.
5. **`Object Payload Bytes` (Longitud igual a `Payload Length`):** Datos brutos de aplicación.

> **Sobrecarga fija de Objeto:** $\mathbf{8\text{ bytes}}$.

---

## 4. Ejemplo Concreto: Transmisión de Telemetría (Sensor IoT)

Imaginemos un sensor de temperatura que reporta una lectura de 16 bytes:
`{"temp": 24.5, "hum": 60}` serializado en CBOR o binario compacto (ej. 16 bytes).

### Balance de Bytes en IPVN7-v0 sobre UDP/IPv4:
- Encabezado IPv4: **20 bytes**
- Encabezado UDP: **8 bytes**
- Cabecera Contenedor IPVN7: **16 bytes**
- Cabecera Objeto IPVN7: **8 bytes**
- Datos del Sensor: **16 bytes**
- Tag Criptográfico Poly1305: **16 bytes**
- **TOTAL EN EL CABLE:** $20 + 8 + 16 + 8 + 16 + 16 = \mathbf{84\text{ bytes}}$.

### Comparativa Teórica Frente a HTTP/2 + TLS 1.3 sobre TCP:
- Encabezado IPv4: 20 bytes
- Encabezado TCP: 20 bytes
- Registro TLS 1.3 (Header + Tag): 5 + 16 = 21 bytes
- Frame Header HTTP/2: 9 bytes
- Encabezados HTTP comprimidos (HPACK estático mínimo): ~20 bytes
- Carga JSON: 26 bytes
- **TOTAL EN EL CABLE:** $20 + 20 + 21 + 9 + 20 + 26 = \mathbf{116\text{ bytes}}$.

> **Ganancia inicial teórica:** El frame IPVN7 requiere 84 bytes frente a 116 bytes de HTTP/2+TLS (reducción de un **27.6%** en bytes transmitidos por paquete periódico en régimen estacionario, sin contar la eliminación completa del handshake TCP de 3 vías).

---

## 5. Primitivas Criptográficas Estándar

1. **Cifrado y Autenticación:**  
   - Primitiva: `ChaCha20-Poly1305` (RFC 8439).
   - Clave: 256 bits (32 bytes).
   - Nonce: 96 bits (12 bytes), compuesto por:
     - 4 bytes de ceros (`0x00000000`).
     - 8 bytes del `Sequence Counter` en Little-Endian.
   - Datos Asociados (AAD): Los 14 bytes exactos de la cabecera de Contenedor.

2. **Ventana Anti-Replay:**  
   - Ventana deslizante de 128 posiciones implementada mediante un bitmask de dos `uint64`.
   - Cualquier datagrama con `Sequence Counter` duplicado o anterior al límite inferior de la ventana es descartado de inmediato sin consumir ciclos de descifrado AEAD.

---

## 6. Siguiente Paso

Con esta especificación binaria formalizada, es posible implementar un **prototipo mínimo en Python** (`scripts/ipvn7/core.py`) restringido exclusivamente a serialización, empaquetado, cifrado AEAD y validación de integridad para ejecutar **`EXP-IPVN7-01`** y **`EXP-IPVN7-02`**.
