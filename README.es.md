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
Mission Group, intercambiar Message en modo full-duplex con sus pares, aceptar elementos WorkItem
explícitos en colas específicas de cada Group y programar trabajo entre distintos Group según su
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
- [21 JSON Schema](schemas/README.md);
- [vectores de conformidad válidos y no válidos](conformance/manifest.json);
- [recursos de marca](assets/brand/).

Las implementaciones deben fijar una versión publicada del protocolo o un commit. Pueden incluir
copias de los JSON Schema y vectores para validación sin conexión, pero esas copias no son
normativas.

## Implementaciones

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) —
  implementación de referencia oficial en Python, runtime de Agent, gateway de Group, ejecutor de
  conformidad y POC.

Las versiones del protocolo y las versiones de las implementaciones se gestionan de forma
independiente. Cada implementación debe publicar una declaración explícita de compatibilidad en
lugar de suponer que dos números de versión iguales implican compatibilidad.

## Conformidad

El manifest contiene actualmente 52 casos: 25 documentos que se espera que sean válidos y 27 que
se espera que sean no válidos. La conformidad estructural con los JSON Schema es necesaria, pero
no suficiente; las implementaciones también deben aplicar las reglas de máquina de estados,
ordenación, epoch, lease, budget, jerarquía, firma y autorización de la especificación.

La implementación en Python puede ejecutar directamente los vectores de este repositorio:

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

También se puede validar desde este repositorio:

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## Licencia

La especificación, los JSON Schema, los vectores de conformidad y los recursos de marca se
distribuyen bajo la licencia [Apache-2.0](LICENSE). La licencia no concede derechos sobre marcas
comerciales.
