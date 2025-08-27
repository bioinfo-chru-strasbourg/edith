#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test des améliorations de performance pour la page d'accueil EDITH
"""

import os
import time
import requests
import statistics
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "http://localhost:5001"  # Ajustez selon votre configuration
NUM_REQUESTS = 20  # Nombre de requêtes à effectuer
CONCURRENCY = 4    # Nombre de requêtes concurrentes

def measure_response_time(endpoint):
    """Mesure le temps de réponse d'un endpoint"""
    start_time = time.time()
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        if response.status_code != 200:
            print(f"ERREUR: {response.status_code} pour {endpoint}")
            return None
        return time.time() - start_time
    except Exception as e:
        print(f"ERREUR: {str(e)} pour {endpoint}")
        return None

def benchmark_endpoint(endpoint, num_requests=10, concurrency=1):
    """Effectue un benchmark sur un endpoint"""
    print(f"\nTest de l'endpoint {endpoint} ({num_requests} requêtes, concurrence={concurrency})")
    
    times = []
    
    # Utiliser ThreadPoolExecutor pour requêtes concurrentes
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(measure_response_time, endpoint) for _ in range(num_requests)]
        for future in futures:
            result = future.result()
            if result is not None:
                times.append(result)
    
    if not times:
        print("Aucun résultat valide")
        return {}
    
    # Calculer les statistiques
    stats = {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "count": len(times),
        "total": sum(times),
        "all_times": times
    }
    
    # Afficher les résultats
    print(f"Temps minimum: {stats['min']:.3f}s")
    print(f"Temps maximum: {stats['max']:.3f}s")
    print(f"Temps moyen: {stats['mean']:.3f}s")
    print(f"Temps médian: {stats['median']:.3f}s")
    
    return stats

def plot_results(results):
    """Génère un graphique des résultats"""
    plt.figure(figsize=(12, 6))
    
    # Premier graphique: temps de réponse moyen par endpoint
    plt.subplot(1, 2, 1)
    endpoints = list(results.keys())
    means = [results[endpoint]['mean'] for endpoint in endpoints]
    plt.bar(endpoints, means, color='blue', alpha=0.7)
    plt.title('Temps de réponse moyen par endpoint')
    plt.ylabel('Temps (secondes)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Deuxième graphique: distribution des temps pour la page d'accueil
    if '/' in results:
        plt.subplot(1, 2, 2)
        home_times = results['/']['all_times']
        plt.hist(home_times, bins=10, color='green', alpha=0.7)
        plt.axvline(results['/']['mean'], color='r', linestyle='dashed', linewidth=1, label=f"Moyenne: {results['/']['mean']:.3f}s")
        plt.title('Distribution des temps de réponse (page d\'accueil)')
        plt.xlabel('Temps (secondes)')
        plt.ylabel('Nombre de requêtes')
        plt.legend()
    
    plt.tight_layout()
    plt.savefig('edith_performance_results.png')
    print("\nGraphique des résultats sauvegardé dans 'edith_performance_results.png'")

def run_benchmarks():
    """Exécute les benchmarks sur différentes routes"""
    print("="*50)
    print("BENCHMARKS DE PERFORMANCE EDITH")
    print("="*50)
    
    results = {}
    
    # Test de la page d'accueil
    results['/'] = benchmark_endpoint('/', NUM_REQUESTS, CONCURRENCY)
    
    # Test de la page statistics
    results['/statistics'] = benchmark_endpoint('/statistics', NUM_REQUESTS, CONCURRENCY)
    
    # Test de la page runs
    results['/runs'] = benchmark_endpoint('/runs', NUM_REQUESTS, CONCURRENCY)
    
    # Test de la page activity
    results['/activity'] = benchmark_endpoint('/activity', NUM_REQUESTS, CONCURRENCY)
    
    # Générer des graphiques
    try:
        plot_results(results)
    except Exception as e:
        print(f"Erreur lors de la génération des graphiques: {str(e)}")
    
    print("\nRÉSUMÉ:")
    for endpoint, stats in results.items():
        if stats:
            print(f"- {endpoint}: {stats['mean']:.3f}s (moyenne), {stats['median']:.3f}s (médiane)")

if __name__ == "__main__":
    run_benchmarks()
