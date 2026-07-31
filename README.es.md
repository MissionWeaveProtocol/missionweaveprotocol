[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | **Español** | [Français](README.fr.md) | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="Icono de MissionWeaveProtocol">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">Sitio web y documentación oficiales</a></strong>
</p>

MissionWeaveProtocol es un protocolo de cooperación orientado a grupos para Agent autónomos que
trabajan dentro de una misma Organization. Cada Agent puede participar simultáneamente en varios
Mission Group, intercambiar Message en modo full-duplex con sus pares, aceptar WorkItem explícitos
en colas específicas de cada Group y programar trabajo entre distintos Group según su
propia política local.

Este repositorio define **MissionWeaveProtocol 0.1**. Su espacio de nombres estable en el protocolo
de comunicación es `missionweaveprotocol`: los identificadores del protocolo usan
`urn:missionweaveprotocol:*` y los tipos de extensión integrados usan
`ext.missionweaveprotocol.*`.

MissionWeaveProtocol no es RPC Agent-to-Agent, enrutamiento físico entre pares, federación ni un
protocolo de consenso distribuido. Una Organization de confianza proporciona identidad, políticas,
autorización, ordenación duradera por Group y responsabilidad humana.

## Artefactos normativos

Este repositorio es la fuente canónica del paquete versionado de artefactos del protocolo:

- [especificación normativa](spec/PROTOCOL.md);
- [glosario del protocolo](CONTEXT.md);
- [22 JSON Schema normativos](schemas/README.md);
- [vectores de conformidad válidos y no válidos](conformance/manifest.json);
- [paquete criptográfico de 22 casos para los nueve perfiles de esquema del Signed Document
  Verification Profile](cryptography/README.md);
- [paquete de primera admisión y confianza histórica con 5 casos y 30
  evaluaciones](admission/README.md);
- [recursos de marca](assets/brand/).

Las implementaciones deben fijar una versión publicada del protocolo o un commit. Pueden incluir
copias de los JSON Schema y vectores para validación sin conexión, pero esas copias no son
normativas.

## Implementaciones

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) —
  implementación de referencia oficial en Python, runtime de Agent, gateway de Group, ejecutor de
  conformidad y POC.
- [MissionWeaveProtocol Go SDK](https://github.com/missionweaveprotocol/go-sdk) — SDK oficial del
  protocolo para Go, con bindings del protocolo y conformidad de schemas y vectores.
- [MissionWeaveProtocol TypeScript SDK](https://github.com/missionweaveprotocol/typescript-sdk) —
  SDK oficial del protocolo para TypeScript, con bindings del protocolo y conformidad de schemas y
  vectores.
- [MissionWeaveProtocol Java SDK](https://github.com/missionweaveprotocol/java-sdk) — SDK oficial
  del protocolo para Java, con bindings del protocolo y conformidad de schemas y vectores.
- [MissionWeaveProtocol Rust SDK](https://github.com/missionweaveprotocol/rust-sdk) — SDK oficial
  del protocolo para Rust, con bindings del protocolo y conformidad de schemas y vectores.
- [MissionWeaveProtocol C++ SDK](https://github.com/missionweaveprotocol/cpp-sdk) — SDK oficial del
  protocolo para C++, con bindings del protocolo y conformidad de schemas y vectores.

Las versiones del protocolo y las versiones de las implementaciones se gestionan de forma
independiente. Cada implementación debe publicar una declaración explícita de compatibilidad en
lugar de suponer que dos números de versión iguales implican compatibilidad.

Python es el runtime de referencia completo. Los SDK de Go, TypeScript, Java, Rust y C++ se centran
actualmente en los bindings del protocolo y la conformidad de schemas y vectores; no declaran una
conformidad completa del comportamiento del runtime.

## Conformidad

El manifest estructural contiene 58 vectores: 27 documentos que se espera que sean válidos y 31 que
se espera que sean no válidos. La conformidad estructural con los JSON Schema es necesaria, pero
no suficiente; las implementaciones también deben aplicar las reglas de máquina de estados,
ordenación, epoch, lease, budget, jerarquía, firma y autorización de la especificación.

El manifest criptográfico independiente contiene 22 casos y 62 evaluaciones que cubren los nueve
perfiles de esquema del Signed Document Verification Profile. Superarlo demuestra la conformidad
con las evaluaciones declaradas a lo largo de las seis etapas de verificación criptográfica de la
sección 6.4.

El manifest de Admission separado contiene 5 casos y 30 evaluaciones para el First-Admission Record
y la confianza histórica, por encima de la verificación criptográfica. Admission permanece
separado de las seis etapas criptográficas. Ninguno de los dos paquetes demuestra la vigencia o el
desfase de reloj de los Command ni la autorización del firmante; esas comprobaciones quedan fuera
de este alcance.

La implementación en Python puede ejecutar directamente los vectores de este repositorio:

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

También se puede validar desde este repositorio:

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: \
  -r requirements-cryptography.lock
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
python scripts/validate_crypto_vectors.py
python scripts/validate_admission_vectors.py
```

## Licencia

La especificación, los JSON Schema, los vectores de conformidad, criptográficos y de Admission, y
los recursos de marca se distribuyen bajo la licencia [Apache-2.0](LICENSE). La licencia no concede
derechos sobre marcas comerciales.
