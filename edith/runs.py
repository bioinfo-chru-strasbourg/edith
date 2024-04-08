import datetime
import glob
import os
import re
import time

# from config.config import folders_runs


def get_directories(root_dir: str, level: int = 1, struct_filter: dict = {}):

    # Init
    directories = {}

    # Fonction pour récupérer les répertoires du niveau spécifié
    def get_directories_at_level(
        directory, current_level: int = 1, struct_filter: dict = {}
    ):
        if current_level == level:
            # Si le niveau actuel correspond au niveau spécifié, récupérer les répertoires à ce niveau
            for entry in os.listdir(directory):
                entry_path = os.path.join(directory, entry)
                if os.path.isdir(entry_path):
                    # Si l'entrée est un répertoire, récupérer les informations et les ajouter au dictionnaire
                    # dir_stat = os.stat(entry_path)
                    # last_modified = time.ctime(os.stat(entry_path).st_mtime)
                    # mtime = os.path.getmtime(entry_path)
                    list_of_files = os.listdir(entry_path)
                    if list_of_files:
                        mtime = max(
                            os.path.getmtime(os.path.join(entry_path, root))
                            for root in list_of_files + [entry_path]
                        )
                    else:
                        mtime = 0
                    last_modified = datetime.datetime.fromtimestamp(mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
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
                if not struct_filter or entry in struct_filter:
                    entry_path = os.path.join(directory, entry)
                    if os.path.isdir(entry_path):
                        get_directories_at_level(
                            entry_path, current_level + 1, struct_filter.get(entry, {})
                        )

    get_directories_at_level(root_dir, 1, struct_filter=struct_filter)
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


def find_most_recent_file(folder: str, pattern: str) -> str:
    """
    This function finds the most recent file in a specified folder that matches a given pattern.

    :param folder: The `folder` parameter should be a string representing the directory path where you
    want to search for files. This is the folder in which you want to find the most recent file
    :type folder: str
    :param pattern: The `pattern` parameter is a string that represents the pattern or format of the
    files you are looking for in the specified `folder`. This pattern can be used to filter out specific
    files based on their names or extensions. For example, if you are looking for text files, the
    pattern could be `
    :type pattern: str
    """

    # if folder and os.path.exists(folder) and os.path.isdir(folder):
    #     path_file = os.path.join(folder, pattern)
    #     files_found = glob.glob(path_file)
    #     if not files_found:
    #         return None
    #     file_most_recent = max(files_found, key=os.path.getmtime)
    #     return file_most_recent
    # else:
    #     return None

    files_found = find_files(folder=folder, pattern=pattern)
    if files_found:
        file_most_recent = max(files_found, key=os.path.getmtime)
        return file_most_recent
    else:
        return None


def find_files(folder: str, pattern: str) -> list:
    """
    This function takes a folder path and a pattern as input, and returns a list of files in the folder
    that match the specified pattern.

    :param folder: The `folder` parameter is a string that represents the directory path where you want
    to search for files. This is the folder in which you want to look for files matching the specified
    pattern
    :type folder: str
    :param pattern: The `pattern` parameter in the `find_files` function is a string that represents the
    pattern or criteria for filtering files within the specified `folder`. This pattern can be used to
    match file names based on specific characters, wildcards, or regular expressions to identify the
    files that meet the specified criteria
    :type pattern: str
    """

    if folder and os.path.exists(folder) and os.path.isdir(folder):
        path_file = os.path.join(folder, pattern)
        files_found = glob.glob(path_file)
        if not files_found:
            return []
        return files_found
    else:
        return []


def get_files_log(folders: dict, exts: list) -> dict:
    """ """

    files_log = {}
    for folder_type in folders:
        for ext in exts:
            key = f"{folder_type}_{ext}"
            # files_log[key] = {}
            files = find_files(
                folder=folders.get(folder_type),
                pattern=f"*ID-*-NAME-*.{ext}",
            )
            for file in files:
                run_name = re.findall(
                    rf".*ID-.*-NAME-(.*)\.{ext}", os.path.basename(file)
                )
                if run_name:
                    if run_name[0] not in files_log:
                        files_log[run_name[0]] = {}
                    last_modified = time.ctime(os.stat(file).st_mtime)
                    mtime = os.path.getmtime(file)
                    files_log[run_name[0]][key] = {
                        "path": file,
                        "mtime": mtime,
                        "last_modified": last_modified,
                    }
    return files_log
