<img src="./assets/laas_logo.png" alt="Logo Laas" width="200"/>
<br></br>

# Intent-Based Network Agent (Clab Agent)


Intelligence Artificielle pour la Modélisation de Réseaux Intent-Based avec ContainerLab


*Système d'agent intelligent développé au LAAS-CNRS pour automatiser la génération et le déploiement de topologies réseau à partir de langage naturel.*

### 👨‍🎓 Auteur
Nathan dos Reis Ruba \
Étudiant-Ingénieur en Automatique-Électronique Systèmes Embarqués\
<b>Spécialisation :</b> Cybersecurité (M2 TLS-SEC)

📍 INSA Toulouse - Institut National des Sciences Appliquées

✉️ Email : nathan.ruba2003@gmail.com \
🔗 LinkedIn : [Nathan dos Reis Ruba](https://www.linkedin.com/in/nathan-dos-reis-ruba-1062b7145/)


## 🎓 Contexte Académique
Ce projet a été développé dans le cadre d'un stage de 3 mois au LAAS-CNRS (Laboratoire d'Analyse et d'Architecture des Systèmes) à Toulouse, France.

### 🏛️ Instituition
- École d'ingénieur: INSA Toulouse
- Laboratoire: LAAS-CNRS, Toulouse
- Équipe: Services et Architectures pour les Réseaux Avancés (SARA)
- Année: 2025

## 📦 Installation

### 1. Prérquis Système
- <b>Système d'exploitation:</b>    Linux Distro (Ubuntu recommended)


```bash
# ContainerLab
sudo bash -c "$(curl -sL https://get.containerlab.dev)" -- -v 0.69.3

# Ollama pour LLMs locaux
curl -fsSL https://ollama.com/install.sh | sh

# Modèles requis
ollama pull qwen3:latest
ollama pull qwen2.5:3b  
ollama pull qwen2.5-coder:3b
```

### 2. Environnement Python
```bash
# Cloner le projet
git clone https://github.com/nathanreisruba/clab_agent.git
cd clab_agent

# Environnement virtuel
python -m venv venv
source venv/bin/activate

# Dépendances
pip install -r requirements.txt
```

### 3. Configuration Google Cloud
```bash
# Authentification pour Dialogflow
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### 4. Import DialogFlow Project
Go to `src/intent_classifier.zip` and import the files to [DialogFlow](https://dialogflow.cloud.google.com/).

### 5. IMPORTANT: configure the DialogFlow
Open `src/tools/models.py` and set:

```python
 # Google Cloud project configuration
    PROJECT_ID = "" # Dialogflow project ID
    SESSION_ID = "" # Static session for consistent context
    LANG = "en" # Language code for input processing
```


## 📚 Documentation Technique

### Structure du Projet
```
clab_agent/
├── src/
│   ├── main.py                 # Point d'entrée principal
│   ├── nodes/
│   │   ├── orchestrator.py     # Module de planification
│   │   ├── researcher.py       # Module de recherche
│   │   ├── runner.py          # Module d'exécution
│   │   ├── schema.py          # Modèles Pydantic
│   │   └── instructions/      # Prompts LLM
│   └── tools/
│       ├── db.py              # Interface ChromaDB
│       ├── models.py          # Gestion LLMs
│       └── scrapy_documentation.py
├── requirements.txt           # Dépendances Python
└── README.md                 # Documentation
```
### Diagramme du Projet
<br></br>
<img src="./assets/diagramme.svg" alt="Diagramme"/>
<br></br>
<br></br>
- <b>Orchestrator :</b> module responsable
d’interpréter, d’expliquer, d’identifier
et de planifier l’objectif de
l’utilisateur.
- <b>Research :</b> module responsable de
consommer des données actualisées
de la base de données, de classer les
meilleures informations et de les
résumer.
- <b>Runner :</b> module responsable de
coder, de vérifier les dépendances
d’exécution et de réaliser le
déploiement.

### Technologies Utilisées
#### Intelligence Artificielle

- 🦙 Ollama : Serveur LLMs locaux (Qwen 3, Qwen 2.5, Qwen 2.5-Coder)
- 🌐 Google Dialogflow : Classification d'intentions
- 🔗 LangChain : Orchestration de chaînes LLM
- 📊 Sentence Transformers : Encodeurs sémantiques cross-domain

#### Base de Données & Recherche

- 🎨 ChromaDB : Base vectorielle pour recherche sémantique
- 🤗 Hugging Face : Modèles d'embeddings (all-MiniLM-L6-v2)
- 📄 Scrapy : Framework d'extraction documentaire

#### Orchestration & Graphes

- 🔄 LangGraph : Graphes d'états pour workflows complexes
- 📐 StateGraph : Gestion des transitions et dépendances
- 🎯 Pydantic : Validation de schémas et modèles de données

#### Conteneurisation & Réseau

- 🐳 Docker API : Gestion programmatique des conteneurs
- 🧪 ContainerLab : Déploiement de topologies réseau

#### Interface & Visualisation

- 🎨 Rich Console : Interface utilisateur avancée en terminal
- 📊 Visualisation Web : Graphiques interactifs des topologies (clab graph)
- ⚡ Live Updates : Feedback temps réel du processus IA

## Résultats

<b>Cas d'Usage Validés:</b> \
"Create a network star topology connected with 10 Mbps maximum"

### YAML Output
```yaml
name: star-bridge-mtu
mgmt:
  network: clab
  ipv4-subnet: 172.20.20.0/24
topology:
  nodes:
    central:
      kind: linux
      image: alpine:latest
      mgmt-ipv4: 172.20.20.11
    node1:
      kind: linux
      image: alpine:latest
      mgmt-ipv4: 172.20.20.12
    node2:
      kind: linux
      image: alpine:latest
      mgmt-ipv4: 172.20.20.13
    node3:
      kind: linux
      image: alpine:latest
      mgmt-ipv4: 172.20.20.14
  links:
    - endpoints: ["central:eth1", "node1:eth1"]
      mtu: 1500
    - endpoints: ["central:eth2", "node2:eth1"]
      mtu: 1500
    - endpoints: ["central:eth3", "node3:eth1"]
      mtu: 1500
```
### Clab Graph
<img src="./assets/clab_graph.jpeg" alt=""/>

### Clab Inspect
| Name | Kind/Image | State | IPv4/6 Address |
| ----------- | ----------- | ----------- | ----------- |
| clab_star-bridge-mtu-central | linux alpine:latest | created | N/A |
| clab_star-bridge-mtu-node1 | linux alpine:latest | created | N/A |
| clab_star-bridge-mtu-node2 | linux alpine:latest | created | N/A |
| clab_star-bridge-mtu-node3 | linux alpine:latest | created | N/A |

## 🙏 Remerciements

- <b>LAAS-CNRS : </b> Pour l'accueil et les ressources de recherche.
- <b>Tuteurs : </b> Pascal Berthou et Slim Abdellatif.