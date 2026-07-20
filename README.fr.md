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
- [ensemble cryptographique de 22 cas pour les neuf profils de schéma du Signed Document
  Verification Profile](cryptography/README.md) ;
- [ressources de marque](assets/brand/).

Les implémentations doivent fixer une version publiée ou un commit du protocole. Elles peuvent
embarquer les schémas et les vecteurs pour une validation hors ligne, mais ces copies ne sont pas
normatives.

## Implémentations

- [MissionWeaveProtocol Python SDK](https://github.com/missionweaveprotocol/python-sdk) —
  implémentation de référence officielle en Python, environnement d’exécution des Agent, passerelle
  de Group, outil de conformité et preuve de concept.
- [MissionWeaveProtocol Go SDK](https://github.com/missionweaveprotocol/go-sdk) — SDK de protocole
  officiel pour Go, avec bindings de protocole et conformité des schémas et vecteurs.
- [MissionWeaveProtocol TypeScript SDK](https://github.com/missionweaveprotocol/typescript-sdk) —
  SDK de protocole officiel pour TypeScript, avec bindings de protocole et conformité des schémas
  et vecteurs.
- [MissionWeaveProtocol Java SDK](https://github.com/missionweaveprotocol/java-sdk) — SDK de
  protocole officiel pour Java, avec bindings de protocole et conformité des schémas et vecteurs.
- [MissionWeaveProtocol Rust SDK](https://github.com/missionweaveprotocol/rust-sdk) — SDK de
  protocole officiel pour Rust, avec bindings de protocole et conformité des schémas et vecteurs.
- [MissionWeaveProtocol C++ SDK](https://github.com/missionweaveprotocol/cpp-sdk) — SDK de protocole
  officiel pour C++, avec bindings de protocole et conformité des schémas et vecteurs.

Les versions du protocole et des implémentations sont gérées indépendamment. Une implémentation doit
publier une déclaration de compatibilité explicite au lieu de supposer que des numéros de version
identiques impliquent une compatibilité.

Python est l’environnement d’exécution de référence complet. Les SDK Go, TypeScript, Java, Rust et
C++ se concentrent actuellement sur les bindings de protocole et la conformité des schémas et
vecteurs ; ils ne revendiquent pas une conformité comportementale complète de l’environnement
d’exécution.

## Conformité

Le manifeste contient actuellement 56 cas : 26 documents attendus comme valides et 30 attendus
comme invalides. La conformité structurelle aux schémas est nécessaire, mais insuffisante ; les
implémentations doivent également appliquer les règles de machine à états, d’ordonnancement,
d’epoch, d’Execution Lease, de budget, de hiérarchie, de signature et d’autorisation définies dans
la spécification.

Le manifeste cryptographique indépendant contient 22 cas couvrant les neuf profils de schéma du
Signed Document Verification Profile. Sa réussite démontre la conformité aux évaluations déclarées
pour les six étapes de vérification cryptographique de la section 6.4 ; elle ne démontre ni la
validation du First-Admission Record ou de la confiance historique, ni la fraîcheur des Command ou
le contrôle du décalage d’horloge, ni l’autorisation du signataire selon son rôle et les politiques
applicables.

L’implémentation Python peut exécuter directement les vecteurs de ce dépôt :

```bash
uv run --project ../python-sdk missionweaveprotocol-conformance --root .
```

Une validation locale depuis ce dépôt est également disponible :

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: \
  -r requirements-cryptography.lock
python scripts/check_repository_policy.py
python scripts/validate_protocol.py
python scripts/validate_crypto_vectors.py
```

## Licence

La spécification, les schémas, les vecteurs de conformité, les vecteurs cryptographiques et les
ressources de marque sont placés sous licence [Apache-2.0](LICENSE). Cette licence n’accorde aucun
droit sur les marques.
