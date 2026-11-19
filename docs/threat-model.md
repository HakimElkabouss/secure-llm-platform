# Modèle de menaces – Secure LLM Platform

> **Version :** 1.0 — **Date :** 15/11/2026 — **Auteur :** Hakim El Kabouss
> **Statut :** en vigueur. Ce document est mis à jour à chaque nouvelle brique du projet.

## 1. Contexte

Ce projet héberge un modèle de langage (LLM) open source sur notre propre
infrastructure, avec **Ollama** et le modèle **Qwen 2.5 (1,5 milliard de paramètres)**.

**Le problème :** Ollama n'a aucune authentification. Toute personne qui
peut joindre son port (11434) peut tout faire : poser des questions, mais
aussi supprimer, télécharger ou créer des modèles.

**L'objectif :** placer une **gateway** devant le modèle. C'est un point
d'entrée unique qui contrôle chaque requête avant qu'elle n'atteigne le LLM.

## 2. Architecture visée

    Utilisateur ──(clé API)──▶ Gateway ──▶ Ollama (LLM)
                                  │
                                  └──▶ Journaux de sécurité (SIEM)

- Seule la gateway est exposée aux utilisateurs.
- Ollama n'est joignable **que** par la gateway.

## 3. Ce que l'on protège (actifs)

| Actif | Pourquoi c'est important |
|---|---|
| Le modèle et sa configuration | Un modèle modifié ou piégé donnerait de fausses réponses aux utilisateurs |
| La carte graphique (GPU) | Ressource coûteuse et limitée, qui peut être volée ou saturée |
| Les données envoyées par les utilisateurs | Elles peuvent contenir des secrets ou des données personnelles |
| Les instructions internes du modèle | Elles peuvent révéler des règles métier ou des informations sensibles |

## 4. Qui peut nous attaquer (acteurs)

| Acteur | Exemple |
|---|---|
| Attaquant externe sans accès | Un robot qui scanne Internet à la recherche de serveurs Ollama ouverts |
| Utilisateur légitime malveillant | Une personne avec une clé valide qui tente de manipuler le modèle |
| Utilisateur légitime imprudent | Un employé qui colle un mot de passe dans sa question sans y penser |

## 5. Les risques

Les risques sont classés selon le modèle **CIA** :
**C**onfidentialité, **I**ntégrité, **D**isponibilité (*Availability*).

| ID | Catégorie | Risque | Impact |
|---|---|---|---|
| R1 | Intégrité | Création d'un faux modèle via l'API (`/api/create`) | Les utilisateurs reçoivent des réponses contrôlées par l'attaquant |
| R2 | Intégrité | Modification des instructions d'un modèle pour le piéger | Le modèle conseille de mauvaises actions (lien malveillant, etc.) |
| R3 | Intégrité / Disponibilité | Suppression d'un modèle (`/api/delete`) | Service coupé |
| R4 | Disponibilité | Téléchargement de modèles très lourds (`/api/pull`) | Disque plein, serveur hors service |
| R5 | Disponibilité | Envoi massif de requêtes | GPU saturé, utilisateurs bloqués, coûts élevés (*LLMjacking*) |
| R6 | Confidentialité | Lecture de la configuration et des instructions internes (`/api/show`) | Fuite de règles métier ou d'informations sensibles |
| R7 | Confidentialité | Un utilisateur envoie un secret (mot de passe, clé, e-mail) au modèle | Le secret sort de son périmètre et peut réapparaître dans une réponse |
| R8 | Intégrité / Confidentialité | *Prompt injection* : manipuler le modèle avec des phrases comme « ignore tes instructions » | Contournement des règles, fuite d'informations |
| R9 | Toutes | Absence de traces | Une attaque passe inaperçue, aucune enquête possible |

## 6. Les mesures de sécurité

Principe appliqué : **la défense en profondeur**. Aucune mesure n'est
suffisante seule. Chaque couche protège si la précédente échoue.

| ID | Mesure | Risques couverts |
|---|---|---|
| M1 | Ollama n'est pas exposé : il n'est joignable que par la gateway | R1 à R8 |
| M2 | Clé API obligatoire pour utiliser la gateway | R1 à R8 (attaquant externe) |
| M3 | La gateway n'autorise qu'une seule action : poser une question. Toutes les autres routes d'Ollama sont bloquées | R1, R2, R3, R4, R6 |
| M4 | Limite du nombre de requêtes par minute et par clé, et taille maximale d'une question | R5 |
| M5 | Masquage automatique des secrets et données personnelles, dans la question **et** dans la réponse | R7 |
| M6 | Détection des tentatives de *prompt injection* et blocage de la requête | R8 |
| M7 | Journalisation de chaque requête et de chaque blocage, au format JSON, lisible par un SIEM | R9 |

## 7. Risques résiduels

Ce qui reste possible même avec toutes les mesures, à accepter ou à traiter plus tard :

- La détection des *prompt injections* repose d'abord sur des règles simples.
  Une attaque bien formulée peut passer. → Amélioration prévue : un modèle
  spécialisé dans la détection.
- Une clé API volée donne accès au service. → Les limites (M4) et les
  journaux (M7) réduisent et révèlent l'abus.
- Le masquage des secrets ne reconnaît que les formats connus.
- La limite de requêtes (M4) est gardée en mémoire dans la gateway. Elle est
  remise à zéro à chaque redémarrage, et ne fonctionne correctement qu'avec une
  seule copie de la gateway. → Amélioration prévue : un compteur partagé (Redis).

## 8. Références

- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)