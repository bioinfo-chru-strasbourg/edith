# Optimisations de Performance pour EDITH avec Parquet

## Problèmes Initiaux
- L'interface est lente quand il y a plusieurs milliers de runs
- Le chargement de la page d'accueil nécessite trop de temps
- Les statistiques prennent du temps à calculer
- La même information est recalculée à chaque fois

## Solutions Implémentées

### 1. Optimisation de la Lecture des Données Parquet

- **Lecture Unique du Fichier** : Nous avons remplacé plusieurs lectures du fichier Parquet par une seule lecture qui extrait toutes les données nécessaires d'un coup.
- **Fonction `get_home_data`** : Cette fonction optimisée extrait toutes les informations nécessaires à la page d'accueil en une seule lecture du fichier Parquet.
- **Filtrage et Tri Optimisés** : Nous effectuons le tri et la limitation directement dans le DataFrame Parquet, ce qui est beaucoup plus efficace que de charger tous les objets puis les filtrer.

### 2. Système de Cache

- **Mise en Place d'un Cache Global** : Nous avons ajouté un système de cache dans `edith/cache.py` qui permet de mettre en cache les résultats des fonctions coûteuses.
- **Cache pour les Modules** : Le chargement des modules est mis en cache pour éviter de relire le disque à chaque requête.
- **Cache pour les Statistiques d'Activité** : La fonction `activity_stats` est mise en cache pour éviter de recalculer les statistiques à chaque fois.
- **Cache pour la Page d'Accueil** : Les données complètes de la page d'accueil sont mises en cache pendant 10 secondes, ce qui permet de servir les pages très rapidement sans recalculer toutes les données.

### 3. Structure Cohérente des Données

- **Uniformisation des Structures de Données** : Nous avons fait en sorte que les routes `/` et `/statistics` utilisent la même structure pour les données `repos`, ce qui facilite la maintenance et évite les bugs.

### 4. Décorateurs pour Mise en Cache Automatique

- **Décorateur `@cached`** : Nous avons créé un décorateur qui permet de mettre en cache facilement les résultats des fonctions.
- **Application du Décorateur** : Nous avons appliqué ce décorateur aux fonctions les plus coûteuses comme `activity_stats` et la route `home`.

### 5. Amélioration des Performances

- **Optimisation pour les Grands Ensembles de Données** : Les optimisations sont particulièrement efficaces pour les grands ensembles de données (milliers de runs).
- **Monitoring des Performances** : Nous avons ajouté des mesures du temps d'exécution pour suivre les performances.
- **Tests de Performance** : Nous avons créé un script `test_response_performance.py` pour mesurer et comparer les temps de réponse des différentes routes.

## Résultats Attendus

- **Page d'Accueil Plus Rapide** : La page d'accueil devrait charger beaucoup plus rapidement, même avec des milliers de runs.
- **Réduction de la Charge CPU et Mémoire** : Les optimisations réduisent l'utilisation des ressources du serveur.
- **Meilleure Expérience Utilisateur** : L'interface est plus réactive, ce qui améliore l'expérience utilisateur.
- **Scalabilité Améliorée** : L'application est maintenant capable de gérer un nombre beaucoup plus important de runs sans ralentissement significatif.

## Prochaines Étapes Possibles

- **Pagination Côté Client** : Implémenter une vraie pagination côté client pour les listes de runs.
- **Cache Redis** : Remplacer notre cache simple par un cache Redis pour une meilleure scalabilité.
- **Pre-calcul des Statistiques** : Pré-calculer les statistiques lors de l'ajout ou de la modification des runs.
- **API GraphQL** : Implémenter une API GraphQL pour permettre au client de demander seulement les données dont il a besoin.
