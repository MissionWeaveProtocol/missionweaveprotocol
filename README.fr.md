[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Español](README.es.md) | **Français** | [Deutsch](README.de.md)

# MissionWeaveProtocol

<p align="center">
  <img src="assets/brand/missionweaveprotocol-icon.svg" width="160" alt="Icône de MissionWeaveProtocol">
</p>

<p align="center">
  <strong><a href="https://missionweaveprotocol.github.io/">Site officiel et documentation</a></strong>
</p>

MissionWeaveProtocol est un protocole de coopération orienté Group pour des Agent autonomes qui
travaillent au sein d’une même Organization. Les Agent peuvent participer à plusieurs Mission
Group, échanger des Message en duplex intégral avec leurs pairs, accepter des WorkItem explicites
dans des files propres à chaque Group et planifier le travail entre les Group selon leur propre
politique locale.

Ce dépôt définit **MissionWeaveProtocol 0.1**. Son espace de noms stable sur le réseau est
`missionweaveprotocol` : les identifiants du protocole utilisent `urn:missionweaveprotocol:*` et les
types d’extension intégrés utilisent `ext.missionweaveprotocol.*`.

MissionWeaveProtocol n’est ni un RPC entre Agent, ni un routage physique pair à pair, ni une
fédération, ni un protocole de consensus distribué. Une Organization de confiance fournit
l’identité, la politique, l’autorisation, l’ordre durable des Group et la responsabilité humaine.

## Artefacts normatifs

Ce dépôt est la source de vérité pour l’ensemble versionné des artefacts du protocole :

- [spécification normative](spec/PROTOCOL.md) ;
- [glossaire du protocole](CONTEXT.md) ;
- [21 schémas JSON](schemas/README.md) ;
- [vecteurs de conformité valides et invalides](conformance/manifest.json) ;
- [ressources de marque](assets/brand/).

Les implémentations doivent fixer une version publiée ou un commit du protocole. Elles peuvent
embarquer les schémas et les vecteurs pour une validation hors ligne, mais ces copies ne sont pas
normatives.

## Implémentations

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) —
  implémentation de référence officielle en Python, environnement d’exécution des Agent, passerelle
  de Group, outil de conformité et preuve de concept.

Les versions du protocole et des implémentations sont gérées indépendamment. Une implémentation doit
publier une déclaration de compatibilité explicite au lieu de supposer que des numéros de version
identiques impliquent une compatibilité.

## Conformité

Le manifeste contient actuellement 52 cas : 25 documents attendus comme valides et 27 attendus
comme invalides. La conformité structurelle aux schémas est nécessaire, mais insuffisante ; les
implémentations doivent également appliquer les règles de machine à états, d’ordonnancement,
d’epoch, d’Execution Lease, de budget, de hiérarchie, de signature et d’autorisation définies dans
la spécification.

L’implémentation Python peut exécuter directement les vecteurs de ce dépôt :

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

Une validation locale au dépôt est également disponible :

```bash
python -m pip install -r requirements-validation.txt
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
```

## Licence

La spécification, les schémas, les vecteurs de conformité et les ressources de marque sont placés
sous licence [Apache-2.0](LICENSE). Cette licence n’accorde aucun droit sur les marques.
