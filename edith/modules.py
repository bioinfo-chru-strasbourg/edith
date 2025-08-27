import os
import yaml
import time
from functools import lru_cache

# Cache pour les modules avec une durée de validité (TTL)
_modules_cache = {}
_modules_cache_time = 0
_MODULES_CACHE_TTL = 60  # 60 secondes de mise en cache

@lru_cache(maxsize=16)
def get_modules_cached(folder, refresh=False) -> dict:
    """Version mise en cache de get_modules pour améliorer les performances"""
    global _modules_cache, _modules_cache_time
    
    current_time = time.time()
    
    # Si le cache est valide et que nous n'avons pas besoin de rafraîchir
    if folder in _modules_cache and current_time - _modules_cache_time < _MODULES_CACHE_TTL and not refresh:
        return _modules_cache[folder]
    
    # Sinon, charger les modules et mettre à jour le cache
    modules = get_modules(folder)
    _modules_cache[folder] = modules
    _modules_cache_time = current_time
    
    return modules

def get_modules(folder) -> dict:
    """Charge les informations sur les modules à partir du dossier spécifié"""
    if not folder or not os.path.isdir(folder):
        return {}
    
    modules = {}

    try:
        for module in os.listdir(folder):
            if os.path.isdir(os.path.join(folder, module)) and os.path.isfile(
                os.path.join(folder, module, "STARK.module")
            ):
                module_config_file = os.path.join(folder, module, "STARK.module")
                try:
                    with open(module_config_file) as f:
                        module_config = yaml.safe_load(f)

                    modules[module] = module_config
                    modules[module]["submodules"] = {}

                    for submodule in os.listdir(os.path.join(folder, module)):
                        if os.path.isdir(
                            os.path.join(folder, module, submodule)
                        ) and os.path.isfile(
                            os.path.join(folder, module, submodule, "STARK.module")
                        ):
                            submodule_config_file = os.path.join(
                                folder, module, submodule, "STARK.module"
                            )
                            try:
                                with open(submodule_config_file) as f:
                                    submodule_config = yaml.safe_load(f)

                                    for submodule_config_entry in submodule_config.get(
                                        "submodules", {}
                                    ):
                                        modules[module]["submodules"][
                                            submodule_config_entry
                                        ] = submodule_config.get("submodules", {}).get(
                                            submodule_config_entry, {}
                                        )
                            except Exception as e:
                                print(f"warning: Module '{module}/{submodule}' not loaded: {str(e)}")
                except Exception as e:
                    print(f"warning: Module '{module}' not loaded: {str(e)}")
    except Exception as e:
        print(f"Error loading modules from {folder}: {str(e)}")
        return {}
        
    return modules
