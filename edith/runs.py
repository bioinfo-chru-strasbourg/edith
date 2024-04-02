import os
import time

# from glob import glob


def generer_structure_repertoires(chemin, niveau_max=None, niveau_actuel=0):
    if niveau_max is not None and niveau_actuel >= niveau_max:
        return {}

    structure = {}
    for nom_dossier in os.listdir(chemin):
        chemin_absolu = os.path.join(chemin, nom_dossier)
        if os.path.isdir(chemin_absolu):
            structure[nom_dossier] = generer_structure_repertoires(
                chemin_absolu, niveau_max, niveau_actuel + 1
            )

    return structure


def construire_dict_dernier_repertoire(chemin, niveau_max=None):
    structure = generer_structure_repertoires(chemin, niveau_max)
    dict_derniers_repertoires = {}

    def parcourir_structure(structure, chemin_actuel):
        for nom_repertoire, sous_structure in structure.items():
            chemin_suivant = os.path.join(chemin_actuel, nom_repertoire)
            if not sous_structure:
                nom_dernier_repertoire = nom_repertoire
                # if nom_dernier_repertoire not in dict_derniers_repertoires:
                #     dict_derniers_repertoires[nom_dernier_repertoire] = []
                dict_derniers_repertoires[nom_dernier_repertoire] = chemin_suivant[
                    len(chemin) + 1 : -1
                ].split("/")
            else:
                parcourir_structure(sous_structure, chemin_suivant)

    parcourir_structure(structure, chemin)
    return dict_derniers_repertoires


def get_runs(folder: str = "/runs", type: str = "input") -> dict:
    """
    This function retrieves a list of subfolders within a specified directory.

    :param folder: The `folder` parameter in the `get_runs` function is a string that represents the
    directory path where the function will look for subfolders. If no folder path is provided, it
    defaults to "/runs", defaults to /runs
    :type folder: str (optional)
    :return: The function `get_runs` is returning a list of subfolders within the specified `folder`
    directory. If the `folder` is a valid directory, it will return a list of subfolder names. If the
    `folder` is not valid or does not exist, an empty list will be returned.
    """

    if folder and os.path.isdir(folder):
        if type.lower() in ["repository", "archives"]:
            folder_level = 3
        else:
            folder_level = 1
        # subfolders = [
        #     os.path.basename(f.path) for f in os.scandir(folder) if f.is_dir()
        # ]
        structure = construire_dict_dernier_repertoire(
            chemin=folder, niveau_max=folder_level
        )
        subfolders = {}
        for run in structure:
            if type.lower() in ["repository", "archives"]:
                subfolders[run] = {
                    "group": structure.get(run)[0],
                    "project": structure.get(run)[1],
                }
            else:
                subfolders[run] = {}
    else:
        subfolders = {}
    return subfolders


# def find_path_infos(path, level_max=None, level=0):
#     if level_max is not None and level >= level_max:
#         return {}

#     structure = {}
#     for my_folder in os.listdir(path):
#         absolute_path = os.path.join(path, my_folder)
#         print(f"absolute_path={absolute_path}")
#         if level_max == level + 1:
#             print(f"absolute_path FOUND ={absolute_path}")

#         if os.path.isdir(absolute_path):
#             structure[my_folder] = find_path_infos(absolute_path, level_max, level + 1)

#     return structure


# def get_directories_old(root_dir, level):
#     directories = {}
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         # Vérifier le niveau
#         depth = dirpath.replace(root_dir, "").count(os.sep)
#         if depth == level:
#             for dirname in dirnames:
#                 dir_fullpath = os.path.join(dirpath, dirname)
#                 # dir_stat = os.stat(dir_fullpath)
#                 # last_modified = time.ctime(dir_stat.st_mtime)
#                 last_modified = "truc"  # os.path.getmtime(dir_fullpath)
#                 directories[dirname] = {
#                     "path": dir_fullpath,
#                     "last_modified": last_modified,
#                 }
#     return directories


# def get_directories_old2(root_dir, level):
#     directories = {}
#     # if level == 0:
#     #     # Si le niveau demandé est 0, on récupère simplement le répertoire racine
#     #     dir_stat = os.stat(root_dir)
#     #     last_modified = time.ctime(dir_stat.st_mtime)
#     #     directories[os.path.basename(root_dir)] = {
#     #         "path": root_dir,
#     #         "last_modified": last_modified,
#     #     }
#     #     return directories

#     # Liste tous les répertoires au niveau demandé
#     for entry in os.listdir(root_dir):
#         entry_path = os.path.join(root_dir, entry)
#         if os.path.isdir(entry_path):
#             # Si l'entrée est un répertoire, récupère les informations et les ajoute au dictionnaire
#             # dir_stat = os.stat(entry_path)
#             # last_modified = time.ctime(dir_stat.st_mtime)
#             last_modified = os.path.getmtime(entry_path)
#             directories[entry] = {"path": entry_path, "mtime": last_modified}

#     return directories


def get_directories(root_dir: str, level: int = 1):
    directories = {}
    # if level == 0:
    #     # Si le niveau demandé est 0, on récupère simplement le répertoire racine
    #     dir_stat = os.stat(root_dir)
    #     last_modified = time.ctime(dir_stat.st_mtime)
    #     directories[os.path.basename(root_dir)] = {
    #         "path": root_dir,
    #         "last_modified": last_modified,
    #     }
    #     return directories

    # Fonction pour récupérer les répertoires du niveau spécifié
    def get_directories_at_level(directory, current_level):
        if current_level == level:
            # Si le niveau actuel correspond au niveau spécifié, récupérer les répertoires à ce niveau
            for entry in os.listdir(directory):
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path):
                    # Si l'entrée est un répertoire, récupérer les informations et les ajouter au dictionnaire
                    # dir_stat = os.stat(entry_path)
                    last_modified = time.ctime(os.stat(entry_path).st_mtime)
                    mtime = os.path.getmtime(entry_path)
                    # if samples:
                    #     nb_samples = count_directories(directory=entry_path)
                    # else:
                    #     nb_samples = None
                    directories[entry] = {
                        "path": entry_path,
                        "mtime": mtime,
                        "last_modified": last_modified,
                    }
        else:
            # Sinon, parcourir récursivement les sous-répertoires
            for entry in os.listdir(directory):
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path):
                    get_directories_at_level(entry_path, current_level + 1)

    get_directories_at_level(root_dir, 1)
    return directories


def count_directories(directory):
    # Liste tous les éléments dans le répertoire
    all_items = os.listdir(directory)

    # Filtre les éléments pour ne garder que les répertoires
    directories = [
        item for item in all_items if os.path.isdir(os.path.join(directory, item))
    ]

    # Compte le nombre de répertoires
    num_directories = len(directories)

    return num_directories


# def get_runs_folder(folder, level=1):
#     # struct = find_path_infos(path=folder, level_max=level)
#     struct = get_directories(root_dir=folder, level=level)
#     #print(f"struct={struct}")
#     return struct
#     # for run in struct:
#     #     print(f"run={run}")
