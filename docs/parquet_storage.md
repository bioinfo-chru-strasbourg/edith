# Guide : Utilisation du stockage Parquet dans EDITH

## Introduction

Ce guide explique comment utiliser le nouveau système de stockage basé sur Parquet dans EDITH, qui remplace la base de données SQLite originale par des fichiers Parquet plus performants.

## Configuration requise

Pour utiliser le stockage Parquet, vous devez installer les dépendances suivantes :

```bash
pip install pandas pyarrow
```

Ces packages sont inclus dans le fichier `requirements.txt` mis à jour.

## Configuration

Le système de stockage Parquet est configuré via le fichier de configuration JSON dans la clé `app.PARQUET_PATH` :

```json
{
  "app": {
    "PARQUET_PATH": "instance"
  }
}
```

Ce chemin indique où les fichiers Parquet seront stockés. Par défaut, ils sont enregistrés dans le dossier `instance` de l'application.

## Utilisation dans le code

Le système de stockage Parquet fonctionne avec une API similaire à SQLAlchemy pour faciliter la transition :

### Récupération d'enregistrements

```python
# Récupérer un utilisateur par ID
user = Users.get(user_id)

# Récupérer tous les utilisateurs
users = Users.query().all()

# Récupérer un utilisateur par nom d'utilisateur
user = Users.query().filter_by(username='admin').first()

# Récupérer des analyses avec filtrage
runs = Runs.query().filter_by(group='DIAG', project='EXOME').all()
```

### Création d'enregistrements

```python
# Créer un nouvel utilisateur
user = Users()
user.username = 'newuser'
user.password = hashlib.sha256('password'.encode('UTF-8')).hexdigest()
user.email = 'user@example.com'
user.is_admin = False
user.save()
```

### Mise à jour d'enregistrements

```python
# Mettre à jour un utilisateur existant
user = Users.get(user_id)
user.email = 'newemail@example.com'
user.save()
```

### Suppression d'enregistrements

```python
# Supprimer un utilisateur
user = Users.get(user_id)
user.delete()
```

## Différences avec SQLAlchemy

Bien que l'API soit similaire, certaines fonctionnalités avancées de SQLAlchemy ne sont pas disponibles :

1. Les relations entre tables doivent être gérées manuellement
2. Les requêtes complexes avec jointures doivent être implémentées avec pandas
3. Les transactions ne sont pas supportées (chaque opération est immédiate)

## Migration des données existantes

Pour migrer des données SQLite existantes vers Parquet, un script de migration est disponible (à implémenter). Ce script lit les données de la base SQLite et les convertit au format Parquet.

## Performance

Le stockage Parquet offre plusieurs avantages par rapport à SQLite :

1. Meilleure compression des données
2. Lecture et écriture colonnaires plus efficaces
3. Intégration native avec pandas pour l'analyse de données
4. Support de types de données avancés
