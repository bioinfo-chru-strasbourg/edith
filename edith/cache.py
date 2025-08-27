import time
from functools import wraps

# Système de cache simple pour les opérations fréquentes
class SimpleCache:
    def __init__(self, default_ttl=60):
        """
        Initialise un cache simple avec une durée de vie par défaut pour les entrées
        
        Args:
            default_ttl: Durée de vie par défaut en secondes (60s par défaut)
        """
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
    
    def get(self, key, default=None):
        """
        Récupère une valeur du cache si elle est toujours valide
        
        Args:
            key: La clé à rechercher
            default: Valeur à retourner si la clé n'existe pas ou est expirée
            
        Returns:
            La valeur en cache ou la valeur par défaut
        """
        if key in self.cache and time.time() - self.timestamps.get(key, 0) < self.default_ttl:
            return self.cache[key]
        return default
    
    def set(self, key, value, ttl=None):
        """
        Stocke une valeur dans le cache
        
        Args:
            key: La clé sous laquelle stocker la valeur
            value: La valeur à stocker
            ttl: Durée de vie en secondes (utilise default_ttl si None)
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
    def invalidate(self, key=None):
        """
        Invalide une entrée spécifique ou tout le cache
        
        Args:
            key: La clé à invalider, ou None pour invalider tout le cache
        """
        if key is None:
            self.cache = {}
            self.timestamps = {}
        elif key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            
    def is_valid(self, key):
        """
        Vérifie si une clé est dans le cache et est toujours valide
        
        Args:
            key: La clé à vérifier
            
        Returns:
            True si la clé existe et n'est pas expirée, False sinon
        """
        return key in self.cache and time.time() - self.timestamps.get(key, 0) < self.default_ttl

# Créer une instance globale du cache
app_cache = SimpleCache()

# Décorateur pour mettre en cache les résultats de fonction
def cached(ttl=60, key_prefix=''):
    """
    Décore une fonction pour mettre en cache son résultat
    
    Args:
        ttl: Durée de vie du cache en secondes
        key_prefix: Préfixe de la clé pour le cache
        
    Returns:
        La fonction décorée
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Créer une clé de cache basée sur les arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Vérifier si le résultat est en cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Si pas en cache, exécuter la fonction et mettre en cache le résultat
            result = func(*args, **kwargs)
            app_cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
