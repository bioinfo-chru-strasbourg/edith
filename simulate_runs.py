#!/usr/bin/env python3
"""
Script pour simuler une base de données de runs avec des exemples fictifs pour EDITH.
Ce script génère des données fictives et les enregistre dans un fichier Parquet.
"""

import os
import pandas as pd
import numpy as np
import datetime
import random
import zlib
from pathlib import Path

# Définir le chemin où enregistrer le fichier Parquet
PARQUET_PATH = "instance/simulated_runs.parquet"
NUM_RUNS = 10000  # Nombre de runs à générer

# Assurons-nous que le répertoire instance existe
os.makedirs("instance", exist_ok=True)

# Définir des valeurs fictives pour les runs
run_names = [
    f"{random.choice(['210', '220', '230'])}{random.randint(1, 12):02d}{random.randint(1, 28):02d}_M{random.randint(1000, 9999)}_{random.randint(100, 999)}_000000000-{chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}{chr(65 + random.randint(0, 25))}"
    for _ in range(NUM_RUNS - 3)
] + ["RUN_TEST", "RUN_DEMO", "RUN_DEVELOPMENT"]

projects = ["HEMATOLOGY", "CARDIOLOGY", "NEUROLOGY", "ONCOLOGY", None]
groups = ["SOMATIC", "GERMLINE", "RESEARCH", "DIAGNOSTIC", None]
status_values = ["secondary", "info", "warning", "success", "danger", None]

# Générer des timestamps entre 2023 et 2025
def random_timestamp():
    """Génère un timestamp aléatoire entre 2023 et 2025"""
    days_back = random.randint(0, 365 * 2)  # Entre maintenant et 2 ans en arrière
    random_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    return random_date.timestamp()

# Fonction pour formater un timestamp en date lisible
def format_timestamp(timestamp):
    """Convertit un timestamp en format de date lisible"""
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

# Générer un contenu de samplesheet fictif
def generate_samplesheet():
    """Génère un contenu de samplesheet fictif"""
    return """[Header]
IEMFileVersion,4
Investigator Name,Dr Smith
Project Name,DNA Sequencing
Experiment Name,WES
Date,01/01/2023
Workflow,GenerateFASTQ
Application,NextSeq FASTQ Only
Assay,TruSeq DNA PCR-Free
Description,Whole Exome Sequencing
Chemistry,Amplicon

[Reads]
151
151

[Settings]
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,Index_Plate,Index_Plate_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample1,Patient1,,,,,D701,ATTACTCG,D501,TATAGCCT,SOMATIC,
Sample2,Patient2,,,,,D702,TCCGGAGA,D502,ATAGAGGC,SOMATIC,
Sample3,Patient3,,,,,D703,CGCTCATT,D503,CCTATCCT,GERMLINE,
"""

# Générer un contenu RTAComplete fictif
def generate_rtacomplete():
    """Génère un contenu RTAComplete fictif"""
    date = format_timestamp(random_timestamp())
    return f"{date.split()[0].replace('-', '/')},{date.split()[1]},Illumina RTA 1.18.42\n\n"

# Générer un STARKCopyComplete fictif
def generate_starkcomplete():
    """Génère un contenu STARKCopyComplete fictif"""
    date = format_timestamp(random_timestamp())
    date_str = date.replace("-", "").replace(":", "").replace(" ", "-")
    duration = f"{random.randint(0, 5):02d}h{random.randint(0, 59):02d}m{random.randint(0, 59):02d}s"
    return f"[{date_str}] Copy complete in {duration}\n\nSTARK analysis completed successfully.\n"

# Générer un contenu d'analysislog fictif
def generate_analysislog():
    """Génère un contenu d'analysislog fictif compressé avec zlib"""
    log_content = f"""
========================================
STARK Analysis Log
========================================
Date: {format_timestamp(random_timestamp())}
Run: STARK Analysis Pipeline
Version: v1.0.0

----------------------------------------
Step 1: FastQC
----------------------------------------
Processing FastQ files...
FastQC completed successfully.

----------------------------------------
Step 2: BWA Alignment
----------------------------------------
Aligning reads to reference genome...
Alignment completed successfully.

----------------------------------------
Step 3: Variant Calling
----------------------------------------
Calling variants with GATK HaplotypeCaller...
Variant calling completed successfully.

----------------------------------------
Step 4: Variant Annotation
----------------------------------------
Annotating variants with VEP...
Annotation completed successfully.

----------------------------------------
Summary
----------------------------------------
Total reads: {random.randint(10000000, 100000000)}
Mapped reads: {random.randint(9000000, 10000000)}
Duplicates: {random.randint(100000, 1000000)}
Variants called: {random.randint(10000, 100000)}
SNPs: {random.randint(9000, 90000)}
Indels: {random.randint(1000, 10000)}

Analysis completed with status: SUCCESS
    """
    # Compresser avec zlib
    return zlib.compress(log_content.encode())

# Créer un DataFrame pandas avec les données simulées
data = []
for i, run_name in enumerate(run_names):
    timestamp = random_timestamp()
    repository_path = f"/Users/lebechea/STARK/output/repository/{random.choice(['SOMATIC', 'GERMLINE'])}/{random.choice(['HEMATOLOGY', 'CARDIOLOGY', 'NEUROLOGY', 'ONCOLOGY'])}/{run_name}" if random.random() > 0.2 else None
    archives_path = f"/Users/lebechea/STARK/output/archives/{random.choice(['SOMATIC', 'GERMLINE'])}/{random.choice(['HEMATOLOGY', 'CARDIOLOGY', 'NEUROLOGY', 'ONCOLOGY'])}/{run_name}" if random.random() > 0.4 else None
    
    # Définir les statuts en fonction de l'existence des chemins et d'autres facteurs
    status_sequencing = "success" if random.random() > 0.1 else random.choice(["info", "secondary"])
    status_analysis = "success" if random.random() > 0.2 else random.choice(["info", "danger", "secondary"])
    status_repository = "success" if repository_path else random.choice(["info", "secondary"])
    status_archives = "success" if archives_path else random.choice(["info", "secondary", "danger"])

    # Créer un dict pour chaque run
    run_data = {
        "id": i + 1,
        "name": run_name,
        "mtime": timestamp,
        "last_modified": format_timestamp(timestamp),
        "input_path": f"/Users/lebechea/STARK/input/runs/{run_name}",
        "input_mtime": timestamp - random.randint(0, 3600 * 24 * 30),  # Jusqu'à 30 jours avant
        "input_last_modified": format_timestamp(timestamp - random.randint(0, 3600 * 24 * 30)),
        "input_samplesheet": generate_samplesheet() if random.random() > 0.1 else None,
        "input_rtacomplete": generate_rtacomplete() if random.random() > 0.1 else None,
        "analysis_path": f"/Users/lebechea/STARK/services/stark/stark/analysis/{run_name}" if random.random() > 0.3 else None,
        "analysis_mtime": timestamp - random.randint(0, 3600 * 24 * 15),  # Jusqu'à 15 jours avant
        "analysis_last_modified": format_timestamp(timestamp - random.randint(0, 3600 * 24 * 15)),
        "analysis_api_json": None,
        "analysis_api_info": None,
        "repository_path": repository_path,
        "repository_mtime": timestamp - random.randint(0, 3600 * 24 * 7) if repository_path else 0,  # Jusqu'à 7 jours avant
        "repository_last_modified": format_timestamp(timestamp - random.randint(0, 3600 * 24 * 7)) if repository_path else None,
        "repository_starkcomplete": generate_starkcomplete() if repository_path and random.random() > 0.2 else None,
        "repository_analysislog": generate_analysislog() if repository_path and random.random() > 0.3 else None,
        "archives_path": archives_path,
        "archives_mtime": timestamp if archives_path else 0,
        "archives_last_modified": format_timestamp(timestamp) if archives_path else None,
        "archives_starkcomplete": generate_starkcomplete() if archives_path and random.random() > 0.2 else None,
        "archives_analysislog": generate_analysislog() if archives_path and random.random() > 0.3 else None,
        "project": random.choice(projects),
        "group": random.choice(groups),
        "description": f"Description for {run_name}" if random.random() > 0.7 else None,
        "status_sequencing": status_sequencing,
        "status_analysis": status_analysis,
        "status_repository": status_repository,
        "status_archives": status_archives,
        "samples": random.randint(1, 20) if random.random() > 0.1 else 0,
    }
    data.append(run_data)

# Créer le DataFrame et sauvegarder en format Parquet
df = pd.DataFrame(data)
df.to_parquet(PARQUET_PATH, index=False)

print(f"Base de données de runs simulés créée avec {len(data)} entrées.")
print(f"Fichier Parquet enregistré dans : {PARQUET_PATH}")

# Afficher les noms des runs générés
print("\nNoms des runs générés :")
for name in run_names:
    print(f" - {name}")
