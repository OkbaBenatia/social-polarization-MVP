# Import manuel vérifié — mode d'emploi

> Préparation, conception et programmation : **Dr. Okba Ben Atia**

Ce fichier explique comment alimenter `data/manual_verified_interactions.csv` avec des
interactions **réellement observées** sur les publications déclarées dans `data/sources.json`.

## Règle absolue

**N'inscrivez que ce que vous avez réellement vu sur la publication.** Aucune ligne ne doit être
inventée, extrapolée, complétée « pour faire du volume » ou reconstituée de mémoire. Une ligne
inexacte invalide l'ensemble des résultats empiriques.

## Colonnes

| Colonne | Obligatoire | Contenu |
|---------|-------------|---------|
| `platform` | oui | `facebook`, `x` ou `instagram` |
| `source_id` | oui | identifiant déclaré dans `data/sources.json` (ex. `facebook_002`) |
| `post_id` | oui | identifiant de la publication d'origine (ex. `facebook_002_post`) |
| `interaction_id` | oui | identifiant **unique** de la ligne (ex. `facebook_002_c001`) |
| `source_user` | oui | auteur de l'interaction, tel qu'affiché publiquement |
| `target_user` | non | utilisateur visé (auteur du message parent), vide pour une publication |
| `interaction_type` | oui | `post`, `comment`, `reply`, `mention`, `share`, `repost`, `quote` |
| `text` | non | texte réellement publié (vide si partage sans commentaire) |
| `timestamp` | non | date/heure affichée, format ISO `2026-01-05T18:00:00` |
| `parent_id` | non | `post_id` pour un commentaire, `interaction_id` du parent pour une réponse |
| `url` | oui | URL de la publication |
| `provenance` | oui | `manual_verified` |
| `collection_method` | oui | description courte, ex. `transcription manuelle depuis la page publique` |
| `collected_at` | oui | date de la saisie, format ISO |

## Exemple de structure (à remplacer par vos observations réelles)

Une publication, un commentaire et une réponse à ce commentaire se saisissent ainsi :

```
facebook,facebook_002,facebook_002_post,facebook_002_p001,<auteur>,,post,<texte publié>,2026-08-13T10:00:00,,https://www.facebook.com/share/p/1HYJ6PKM2Q/,manual_verified,transcription manuelle,2026-08-25T12:00:00
facebook,facebook_002,facebook_002_post,facebook_002_c001,<commentateur>,<auteur>,comment,<texte du commentaire>,2026-08-13T10:12:00,facebook_002_post,https://www.facebook.com/share/p/1HYJ6PKM2Q/,manual_verified,transcription manuelle,2026-08-25T12:00:00
facebook,facebook_002,facebook_002_post,facebook_002_r001,<répondant>,<commentateur>,reply,<texte de la réponse>,2026-08-13T10:31:00,facebook_002_c001,https://www.facebook.com/share/p/1HYJ6PKM2Q/,manual_verified,transcription manuelle,2026-08-25T12:00:00
```

Les identifiants d'utilisateurs peuvent rester bruts : ils sont pseudonymisés par le pipeline
avant toute analyse, et n'apparaissent jamais dans `public/data/`.

## Chaîne à exécuter ensuite

```bash
python analysis/collect.py
python analysis/build_real_dataset.py
python analysis/run_analysis.py --input data/real_interactions.csv
```

## Qualité minimale attendue

Le contrôle automatique (`analysis/quality_checks.py`, exécuté par `build_real_dataset.py`)
refuse : une ligne sans `provenance`, une provenance `synthetic_demo`, un `interaction_id`
dupliqué, une interaction sans `source_id` rattaché à `data/sources.json`, et une réponse dont
le `parent_id` ne correspond à aucune ligne du fichier.
