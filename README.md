# 💬 Application de Tchat - Mini Projet Python, MongoDB & Redis

## Description

Ce projet est une application de **messagerie instantanée** développée en **Python** utilisant les bases de données **MongoDB** pour la gestion des messages et **Redis** pour le suivi des utilisateurs connectés. Il s’inscrit dans le cadre d’un mini-projet académique visant à mettre en œuvre :

- Une architecture serveur/client avec **sockets Python**
- La persistance des messages avec **MongoDB**
- Le suivi temps réel des connexions avec **Redis**
- La **tolérance aux pannes** avec un **ReplicaSet MongoDB**

## Technologies utilisées

- Redis (via redis-py)
- MongoDB (avec ReplicaSet)
- Sockets TCP (module `socket`, threading)

## Structure du projet
Le dépôt est organisé en plusieurs branches, chacune correspondant à une fonctionnalité ou un composant spécifique :​

`main` : Branche principale contenant la version stable de l'application.

`develop` : Branche de développement intégrant les dernières fonctionnalités avant leur fusion dans `main`.

`feature/docker-setup` : Configuration de l'environnement Docker pour faciliter le déploiement et l'exécution de l'application.

`feature/frontend-web` : Développement de l'interface utilisateur web pour l'application de tchat.​

`feature/mongodb-schemas` : Définition des schémas de données et intégration de MongoDB pour la gestion des messages.

`feature/redis-tracking` : Implémentation du suivi des connexions des utilisateurs en temps réel à l'aide de Redis.​

Chaque branche est dédiée à une fonctionnalité spécifique, facilitant ainsi le développement collaboratif et la gestion du code.​


## Fonctionnalités attendues
- [ ] Connexion et déconnexion d'utilisateurs
- [ ] Affichage des utilisateurs actuellement en ligne (via Redis)
- [ ] Envoi et réception de messages
- [ ] Stockage des messages dans MongoDB
- [ ] Affichage de l’historique des conversations
- [ ] Requêtes analytiques (utilisateur le plus actif, etc.)
- [ ] Mise en place d’un ReplicaSet MongoDB
