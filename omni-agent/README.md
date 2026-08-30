# OMNI Agent

OMNI Agent est la couche agentique de l'écosystème ABFINI.

## Positionnement

OMNI est construit comme un agent orchestrateur réutilisable. Il peut servir BARDEC, ABFINI et les futurs projets de l'écosystème.

Le dépôt ABFINI contient donc OMNI sous `omni-agent/` : OMNI fait partie de l'écosystème, tout en gardant une architecture modulaire et extractible.

## V0.2 — fondation

Première brique : **OMNI Core**.

Objectifs initiaux :
- recevoir une tâche ;
- créer un plan simple ;
- conserver l'état d'exécution ;
- produire des actions structurées ;
- recevoir les résultats des outils ;
- terminer proprement une tâche ;
- journaliser les événements ;
- préparer l'intégration future des modèles, outils, agents et connecteurs.

## Fournisseurs LLM prévus

- DeepSeek — principal
- OpenRouter — secours
- Anthropic — dernier recours

Aucun fournisseur n'est imposé au Core. Les modèles seront branchés via le Model Layer.

## Architecture cible

```text
OMNI CORE
  ├── Planner
  ├── State
  ├── Permissions
  ├── Tool Router
  ├── Agent Router
  ├── Model Layer
  ├── Memory
  ├── Connectors
  └── Observability
```

## Règle de sécurité

OMNI peut préparer et demander une action, mais les actions sensibles devront passer par un système de permissions et, lorsque requis, une confirmation humaine.

## Évolution

`OMNI Core → Model Router → Tool/Connector Router → Agent Router → Memory/RAG → Social Connectors → Control Center → intégration ABFINI complète`.
