# Optimisations de Performance pour EDITH avec Parquet

## Problème Initial
L'interface EDITH est lente quand il y a plusieurs milliers de runs, car elle charge tous les runs même quand seulement quelques-uns sont affichés.

## Solutions Implémentées

### 1. Optimisation des Routes Principales

#### Page d'accueil `/`
- **Avant** : Chargeait tous les runs puis les filtrait côté Python
- **Après** : Utilise `order_by('mtime').limit(12)` pour ne charger que les 12 runs les plus récents
- **Avantage** : Réduction drastique du temps de chargement et de la mémoire utilisée

#### Page des statistiques `/statistics`
- **Avant** : Chargeait tous les runs pour calculer les statistiques
- **Après** : 
  - Utilise des requêtes spécialisées pour obtenir uniquement les noms des runs
  - Calcule les statistiques directement depuis les fichiers Parquet sans charger les objets

#### Affichage des runs `/runs_<source>`
- **Avant** : Chargeait tous les runs puis les triait
- **Après** : Utilise `order_by().limit(1000)` pour limiter le nombre de runs chargés

### 2. Optimisation du Calcul des Statistiques

#### Fonction `activity_stats`
- **Avant** : Nécessitait une liste complète d'objets run
- **Après** : 
  - Peut travailler directement avec les DataFrames Parquet
  - Utilise des opérations vectorielles pandas pour les comptages
  - Évite de charger tous les runs en mémoire

### 3. Méthodes d'Optimisation Utilisées

1. **Tri et limite côté stockage** : Les opérations `order_by()` et `limit()` sont exécutées directement au niveau du stockage Parquet
2. **Requêtes spécialisées** : Utilisation de `store.execute_query()` pour exécuter du code pandas directement sur les DataFrames
3. **Chargement partiel** : Ne charge que les colonnes et lignes nécessaires
4. **Traitement vectoriel** : Utilisation des opérations pandas pour le traitement en lot

### 4. Script de Test des Performances

Un script `test_parquet_optimizations.py` permet de mesurer et comparer les performances :
- Temps de chargement complet vs. limité
- Calcul des statistiques avec objets vs. avec DataFrame
- Mesure des gains de performances obtenus

## Résultats Attendus

Les optimisations devraient permettre :
1. Un chargement initial beaucoup plus rapide de l'interface
2. Une consommation mémoire réduite
3. Une meilleure réactivité globale de l'application
4. Une capacité à gérer des ensembles de données beaucoup plus volumineux

Ces améliorations seront d'autant plus significatives que le nombre de runs dans la base est important.
