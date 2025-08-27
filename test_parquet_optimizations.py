#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for measuring performance improvements in Parquet optimization
"""

import os
import time
import pandas as pd
from edith.parquet_store import ParquetStore
from edith.parquet_models import ParquetModel, Users, Runs

# Charger le store Parquet (ajustez le chemin si nécessaire)
STORE_PATH = "instance"
store = ParquetStore(STORE_PATH)
ParquetModel.set_store(store)

def test_full_load():
    """Mesurer le temps pour charger tous les runs"""
    start_time = time.time()
    runs = Runs.query().all()
    duration = time.time() - start_time
    print(f"Chargement complet des runs: {len(runs)} runs chargés en {duration:.4f} secondes")
    return duration, len(runs)

def test_limited_load():
    """Mesurer le temps pour charger un nombre limité de runs, triés par mtime"""
    start_time = time.time()
    runs = Runs.query().order_by('mtime', ascending=False).limit(12).all()
    duration = time.time() - start_time
    print(f"Chargement limité des runs: {len(runs)} runs chargés en {duration:.4f} secondes")
    return duration, len(runs)

def test_activity_stats_objects():
    """Mesurer le temps pour calculer les statistiques d'activité avec des objets"""
    # Importer la fonction depuis main.py
    from main import activity_stats
    
    # Charger d'abord 500 runs récents
    runs = Runs.query().order_by('mtime', ascending=False).limit(500).all()
    
    start_time = time.time()
    stats = activity_stats(runs)
    duration = time.time() - start_time
    print(f"Calcul des stats d'activité (avec objets): {duration:.4f} secondes")
    return duration

def test_activity_stats_dataframe():
    """Mesurer le temps pour calculer les statistiques d'activité avec DataFrame"""
    # Importer la fonction depuis main.py
    from main import activity_stats
    
    start_time = time.time()
    stats = activity_stats(use_dataframe=True)
    duration = time.time() - start_time
    print(f"Calcul des stats d'activité (avec DataFrame): {duration:.4f} secondes")
    return duration

def test_specialized_query():
    """Test d'une requête spécialisée pour compter les runs par type"""
    start_time = time.time()
    input_names = store.execute_query('runs', lambda df: df[df['input_path'].notnull()]['name'].tolist())
    repository_names = store.execute_query('runs', lambda df: df[df['repository_path'].notnull()]['name'].tolist())
    archives_names = store.execute_query('runs', lambda df: df[df['archives_path'].notnull()]['name'].tolist())
    duration = time.time() - start_time
    print(f"Requête spécialisée: {len(input_names) + len(repository_names) + len(archives_names)} noms récupérés en {duration:.4f} secondes")
    return duration

def run_benchmarks():
    """Exécuter tous les tests de performance"""
    print("="*50)
    print("BENCHMARKS DE PERFORMANCE PARQUET")
    print("="*50)
    
    # Obtenir le nombre total de runs pour référence
    total_count = Runs.query().count()
    print(f"Nombre total de runs dans la base: {total_count}")
    print("-"*50)
    
    # Tests de chargement
    full_time, full_count = test_full_load()
    limited_time, limited_count = test_limited_load()
    print(f"Amélioration de performance: {full_time/limited_time:.2f}x plus rapide")
    print("-"*50)
    
    # Tests de calcul de statistiques
    if total_count > 0:
        object_time = test_activity_stats_objects()
        df_time = test_activity_stats_dataframe()
        print(f"Amélioration de performance: {object_time/df_time:.2f}x plus rapide")
        print("-"*50)
    
    # Test de requête spécialisée
    specialized_time = test_specialized_query()
    print("-"*50)
    
    print("RÉSUMÉ:")
    print(f"- Nombre total de runs: {total_count}")
    print(f"- Temps de chargement complet: {full_time:.4f}s")
    print(f"- Temps de chargement limité (12 runs): {limited_time:.4f}s")
    if total_count > 0:
        print(f"- Temps de calcul stats (objets): {object_time:.4f}s")
        print(f"- Temps de calcul stats (DataFrame): {df_time:.4f}s")
    print(f"- Temps de requête spécialisée: {specialized_time:.4f}s")
    print("="*50)

if __name__ == "__main__":
    run_benchmarks()
