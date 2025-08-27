import argparse
import datetime
import hashlib
import os
import re
import time
import zlib
import functools
from flask import Flask, render_template, request, url_for, redirect, jsonify, current_app
import pygal
from pygal.style import CleanStyle
import pandas as pd
#from sqlalchemy.sql import func
from edith.cache import app_cache, cached

# from flask_cors import CORS
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from flask_bootstrap import Bootstrap
import yaml
from edith.runs import (
    find_files,
    find_most_recent_file,
    get_directories,
    get_files_log,
)  # , get_runs  # , get_runs_folder
from edith.modules import get_modules_cached as get_modules
from edith.parquet_store import ParquetStore
from edith.parquet_models import ParquetModel, Users, Runs


app = Flask(__name__)

# Fonctions partagées pour gérer les statistiques des runs
def refresh_runs_cache():
    """
    Force le rafraîchissement des caches relatifs aux runs
    À appeler après toute modification des données
    """
    app_cache.invalidate("runs_statistics")
    app_cache.invalidate("home_page_data")
    app_cache.invalidate("statistics_page_data")
    app_cache.invalidate("activity_stats:True")
    app_cache.invalidate("run_status")
    print("Run statistics cache refreshed")

def get_runs_statistics():
    """
    Fonction centralisée pour récupérer les statistiques des runs
    Cette fonction est mise en cache pour de meilleures performances
    """
    cache_key = "runs_statistics"
    cached_stats = app_cache.get(cache_key)
    if cached_stats:
        return cached_stats
        
    # Faire une seule lecture pour obtenir toutes les informations nécessaires
    stats = store.execute_query('runs', lambda df: {
        'total_runs': len(df),
        'input_names': df[df['input_path'].notnull()]['name'].tolist(),
        'repository_names': df[df['repository_path'].notnull()]['name'].tolist(),
        'archives_names': df[df['archives_path'].notnull()]['name'].tolist(),
        'input_count': df['input_path'].notnull().sum(),
        'repository_count': df['repository_path'].notnull().sum(),
        'archives_count': df['archives_path'].notnull().sum()
    })
    
    # Mettre en cache pour une minute
    app_cache.set(cache_key, stats, ttl=60)
    return stats

# Config
config_file = os.environ.get("CONFIG_FILE", os.path.join(app.root_path, "config", "config.json"))
print(f"Loading configuration from {config_file}")
with open(config_file, "r") as config_file_pointer:
    config_json = yaml.safe_load(config_file_pointer)


# All EDITH config
app.config["EDITH"] = config_json

# Parquet storage
parquet_path = config_json.get("app", {}).get("PARQUET_PATH", "instance")
store = ParquetStore(parquet_path)
ParquetModel.set_store(store)  # Set the store for all models

# Secret key
app.config["SECRET_KEY"] = config_json.get("app", {}).get("SECRET_KEY", "abcdef")

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)

# # enable CORS
# CORS(app, resources={r"/*": {"origins": "*"}})


# Models are now imported from edith.parquet_models
# The class definitions in that file replace these

# Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Use Parquet get() method instead of SQLAlchemy query.get()
    return Users.get(user_id)


# class Groups(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     groupname = db.Column(db.String(250), unique=True, nullable=False)


# Runs class is now imported from edith.parquet_models
# Comment out all the following SQLAlchemy definitions as they are now in parquet_models.py
#    input_path = db.Column(db.String(500), unique=False, nullable=True)
#    input_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
#    input_last_modified = db.Column(db.String(100), unique=False, nullable=True)
#    input_samplesheet = db.Column(db.Text, unique=False, nullable=True)
#    input_rtacomplete = db.Column(db.Text, unique=False, nullable=True)
#    repository_path = db.Column(db.String(500), unique=False, nullable=True)
#    repository_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
#    repository_last_modified = db.Column(db.String(100), unique=False, nullable=True)
#    repository_starkcomplete = db.Column(db.Text, unique=False, nullable=True)
#    repository_analysislog = db.Column(db.Text, unique=False, nullable=True)
#    repository_config = db.Column(db.Text, unique=False, nullable=True)
#    archives_path = db.Column(db.String(500), unique=False, nullable=True)
#    archives_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
#    archives_last_modified = db.Column(db.String(100), unique=False, nullable=True)
#    archives_starkcomplete = db.Column(db.Text, unique=False, nullable=True)
#    archives_analysislog = db.Column(db.Text, unique=False, nullable=True)
#    archives_config = db.Column(db.Text, unique=False, nullable=True)
#    analysis_path = db.Column(db.String(500), unique=False, nullable=True)
#    analysis_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
#    analysis_last_modified = db.Column(db.String(100), unique=False, nullable=True)
#    analysis_listener_log = db.Column(db.Text, unique=False, nullable=True)
#    analysis_listener_json = db.Column(db.Text, unique=False, nullable=True)
#    analysis_listener_info = db.Column(db.Text, unique=False, nullable=True)
#    analysis_listener_output = db.Column(db.Text, unique=False, nullable=True)
#    analysis_listener_err = db.Column(db.Text, unique=False, nullable=True)
#    analysis_api_log = db.Column(db.Text, unique=False, nullable=True)
#    analysis_api_json = db.Column(db.Text, unique=False, nullable=True)
#    analysis_api_info = db.Column(db.Text, unique=False, nullable=True)
#    analysis_api_output = db.Column(db.Text, unique=False, nullable=True)
# The complete Runs model is now imported from edith.parquet_models
# No need for db.init_app and db.create_all with ParquetStore

### RUNS

# DATABASE = "database.db"

# def get_db():
#     db = getattr(Flask, "_database", None)
#     if db is None:
#         db = Flask._database = sqlite3.connect(DATABASE)
#     return db

# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(Flask, "_database", None)
#     if db is not None:
#         db.close()


@login_manager.user_loader
def loader_user(user_id):
    try:
        # Handle both integer IDs and float IDs stored as strings
        if '.' in user_id:
            user_id = int(float(user_id))
        else:
            user_id = int(user_id)
        return Users.get(user_id)
    except (ValueError, TypeError):
        return None


# sanity check route
@app.route("/ping", methods=["GET"])
def ping_pong():
    return jsonify("pong!")


@app.route("/test")
def test():
    # cur = get_db().cursor()
    return render_template("main.html")


@app.route("/pygal")
def pygalexample():
    try:
        # graph = pygal.Line()
        # graph.title = "% Change Coolness of programming languages over time."
        # graph.x_labels = ["2011", "2012", "2013", "2014", "2015", "2016"]
        # graph.add("Python", [15, 31, 89, 200, 356, 900])
        # graph.add("Java", [15, 45, 76, 80, 91, 95])
        # graph.add("C++", [5, 51, 54, 102, 150, 201])
        # graph.add("All others combined!", [5, 15, 21, 55, 92, 105])
        # graph_data = graph.render_data_uri()

        # Style
        custom_style = CleanStyle(
            background="transparent",
            plot_background="transparent",
        )

        # By groiups and projects

        pie_chart = pygal.Pie(
            style=custom_style, inner_radius=0.4, width=800, height=800
        )
        pie_chart.title = "Groups and Projects"
        # Replace SQLAlchemy query with pandas operations using ParquetStore
        # Get all runs from Parquet storage
        all_runs = Runs.query().all()
        
        # Group by group and project and count
        # Convert to pandas DataFrame
        df = pd.DataFrame([(run.group, run.project) for run in all_runs], 
                         columns=['group', 'project'])
        
        # Group and count
        if len(df) > 0:
            runs_by_group = df.groupby(['group', 'project']).size().reset_index(name='total')
            # Convert to list of tuples (group, project, count)
            runs_by_group = [(row['group'], row['project'], row['total']) 
                            for _, row in runs_by_group.iterrows()]
        else:
            runs_by_group = []
        # print(runs_by_group)
        runs_by_group_dict = {}
        for group, project, total in runs_by_group:
            if group and project:
                # print(group, project, total)
                if group not in runs_by_group_dict:
                    runs_by_group_dict[group] = {}
                if project not in runs_by_group_dict[group]:
                    runs_by_group_dict[group][project] = 0
                runs_by_group_dict[group][project] += 1

        for group in runs_by_group_dict:
            pie_chart.add(str(group), list(runs_by_group_dict.get(group).values()))

        # runs_by_group_dict = dict(runs_by_group)
        # for group in runs_by_group_dict:
        #     # print(group)
        #     # print(runs_by_group_dict.get(group))
        #     pie_chart.add(str(group), runs_by_group_dict.get(group))
        pie_graph_data = pie_chart.render_data_uri()

        # Activity by month
        runs_mtime = (
            Runs.query.with_entities(
                Runs.mtime, Runs.last_modified, Runs.id, Runs.group, Runs.project
            )
            .order_by(Runs.mtime)
            .all()
        )
        runs_mtime_dict = {}
        runs_mtime_group_dict = {}
        for mtime, last_modified, id, group, project in runs_mtime:
            if group and project or True:
                day = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                month = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m")
                if day not in runs_mtime_dict:
                    runs_mtime_dict[day] = 0
                runs_mtime_dict[day] += 1
                if group not in runs_mtime_group_dict:
                    runs_mtime_group_dict[group] = {}
                if day not in runs_mtime_group_dict[group]:
                    runs_mtime_group_dict[group][day] = 0
                runs_mtime_group_dict[group][day] += 1
        # list_of_mtime = list(dict(runs_by_group).keys())

        r = pd.date_range("2014-10", "2016-01", freq="M").strftime("%Y-%m").tolist()
        print(f"r: {r}")
        date_chart = pygal.Line(
            x_label_rotation=20, fill=True, style=custom_style, width=1600, height=400
        )
        date_chart.title = "Runs activity by month"
        date_chart.x_labels = list(runs_mtime_dict.keys())
        date_chart.add("Total Nb runs", list(runs_mtime_dict.values()))
        for group in runs_mtime_group_dict:
            date_chart.add(f"{group}", list(runs_mtime_group_dict[group].values()))
        date_graph_data = date_chart.render_data_uri()
        # for day in runs_mtime_dict:
        #     date_chart.add("Nb runs", [300, 412, 823, 672])

        # date_chart = pygal.Line(x_label_rotation=20)
        # date_chart.x_labels = map(
        #     lambda d: d.strftime("%Y-%m-%d"),
        #     [
        #         datetime(2013, 1, 2),
        #         datetime(2013, 1, 12),
        #         datetime(2013, 2, 2),
        #         datetime(2013, 2, 22),
        #     ],
        # )
        # date_chart.add("Visits", [300, 412, 823, 672])
        # graph_data = date_chart.render_data_uri()

        # return render_template("graphing.html", graph_data=graph_data)
        return render_template(
            "graphing.html",
            pie_graph_data=pie_graph_data,
            date_graph_data=date_graph_data,
        )

    except Exception as e:
        return str(e)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    user_id = current_user.id

    if request.method == "POST":
        # user_id = request.form.get("id", user_id)
        user = Users.query().filter_by(id=user_id).first()
        result = user.update_profile(dict(request.form))

    else:
        result = {}

    # user = Users.query.filter_by(id=user_id).first()

    return render_template(
        "profile.html",
        success=result.get("success"),
        info=result.get("info"),
        warning=result.get("warning"),
        error=result.get("error"),
    )


@app.route("/populate")
@login_required
def admin_populate():
    user = Users.query().filter_by(id=current_user.id).first()
    if user.is_admin:
        populate()
        return render_template("admin.html", success="Populate OK")
        
@app.route("/cache", methods=["GET", "POST"])
@login_required
def cache_management():
    """Manage the Parquet data cache"""
    user = Users.query().filter_by(id=current_user.id).first()
    if not user.is_admin:
        return redirect(url_for('index'))
        
    # Handle POST request to invalidate cache
    if request.method == "POST":
        table_name = request.form.get("table_name", None)
        store.invalidate_cache(table_name)
        message = f"Cache invalidated for {'all tables' if table_name is None else table_name}"
        return render_template("admin.html", success=message, cache_stats=store.get_cache_stats())
    
    # GET request to show cache statistics
    return render_template("admin.html", cache_stats=store.get_cache_stats())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # All users - Get all and sort by username
        all_users = Users.query().all()
        all_users.sort(key=lambda user: user.username if hasattr(user, 'username') else "")

        # Check admin
        if len(all_users):
            is_admin = False
        else:
            is_admin = True

        # Check username
        username = request.form.get("username")
        user_check = Users.query().filter_by(username=username).first()

        # Create user
        if user_check:
            return render_template(
                "sign_up.html",
                error=f"User '{username}' already exists. Choose another username.",
                username=username,
            )
        else:
            # Create user object and set attributes individually for Parquet
            user = Users()
            user.username = request.form.get("username")
            user.password = hashlib.sha256(
                request.form.get("password").encode("UTF-8")
            ).hexdigest()
            user.is_admin = is_admin
            user.groups = ""
            
            # Use Parquet save instead of db.session.add/commit
            user.save()
        return render_template("login.html", success=f"User '{username}' registered!")

    # TEST
    password = "tata"
    print(hashlib.sha256(password.encode("UTF-8")).hexdigest())

    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    warning = None
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        # password = request.form.get("password")
        password = hashlib.sha256(
            request.form.get("password").encode("UTF-8")
        ).hexdigest()
        user = Users.query().filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("home"))
        else:
            error = f"Error in '{username}' login or password"
    print(f"warning={warning}")
    return render_template("login.html", warning=warning, error=error)


@app.route("/help", methods=["GET", "POST"])
def help():
    return render_template("help.html")


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.is_admin:
        # Get all users and sort by username
        all_users = Users.query().all()
        all_users.sort(key=lambda user: user.username if hasattr(user, 'username') else "")
        return render_template("admin.html", users=all_users)
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/api/refresh")
def api_refresh():
    """
    Endpoint API pour rafraîchir tous les caches
    """
    refresh_runs_cache()
    return jsonify({
        "status": "success", 
        "message": "All caches refreshed", 
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/")
@cached(ttl=10, key_prefix='home_data')
def home():
    # Limit for display
    limit = 12
    start_time = time.time()
    
    # Vérifier si nous avons des données en cache
    cache_key = "home_page_data"
    cached_data = app_cache.get(cache_key)
    
    if cached_data:
        print(f"Using cached home page data (saved {time.time() - app_cache.timestamps.get(cache_key, 0):.3f} seconds ago)")
        return render_template(
            "main.html",
            runs=cached_data['recent_runs'],
            all_runs_names=cached_data['all_runs_names'],
            runs_number=cached_data['total_runs'],
            limit=limit,
            modules=cached_data['modules'],
            repos=cached_data['repos'],
            activity_statistics=cached_data['activity_statistics'],
            runs_mode="table",
        )
    
    # Utiliser une combinaison de deux fonctions optimisées:
    # 1. get_runs_statistics() pour les statistiques générales (partagé avec /statistics)
    # 2. Une fonction spécifique pour obtenir les runs récents
    
    # Obtenir les statistiques générales
    run_stats = get_runs_statistics()
    
    # Fonction pour récupérer uniquement les runs récents
    def get_recent_runs(df, limit=limit):
        """Récupère les runs les plus récents"""
        # Créer une copie sécurisée pour le tri
        df_with_mtime = df.copy()
        df_with_mtime['mtime_safe'] = df_with_mtime['mtime'].fillna(0)
        # Trier et limiter
        return df_with_mtime.sort_values('mtime_safe', ascending=False).head(limit).to_dict('records')
    
    # Récupérer les runs récents
    recent_runs_data = store.execute_query('runs', get_recent_runs)
    
    # Convertir les dictionnaires de runs récents en objets Runs
    recent_runs = []
    for run_data in recent_runs_data:
        run = Runs()
        for key, value in run_data.items():
            setattr(run, key, value)
        recent_runs.append(run)
    
    # Définir repos avec des listes de noms (même structure que dans /statistics)
    repos = {
        "Input": run_stats['input_names'],
        "Repository": run_stats['repository_names'],
        "Archives": run_stats['archives_names']
    }
    
    # Limiter la liste de noms pour la recherche
    all_runs_names = run_stats['input_names'][:1000]  # Limiter à 1000 noms pour performance
    
    # Get activity statistics directly from Parquet files
    # Using the dataframe approach which is more efficient
    activity_statistics = activity_stats(use_dataframe=True)

    # Get modules (cette opération n'est pas liée à Parquet donc on la garde)
    modules = get_modules(folder=config_json.get("modules_dir", ""))
    
    # Stocker les données finales en cache
    app_cache.set(cache_key, {
        'recent_runs': recent_runs,
        'all_runs_names': all_runs_names,
        'total_runs': run_stats['total_runs'],
        'modules': modules,
        'repos': repos,
        'activity_statistics': activity_statistics
    })
    
    # Log du temps d'exécution pour monitoring des performances
    print(f"Home page data prepared in {time.time() - start_time:.3f} seconds")
    
    return render_template(
        "main.html",
        runs=recent_runs,
        all_runs_names=all_runs_names,
        runs_number=run_stats['total_runs'],
        limit=limit,
        modules=modules,
        repos=repos,
        activity_statistics=activity_statistics,
        runs_mode="table",
    )


@app.route("/runs")
@login_required
def runs():
    if current_user.is_authenticated:
        return render_template("runs.html", title="")
    else:
        return redirect(url_for("login"))


@app.route("/runs_<source>")
@login_required
def runs_source(source):
    if current_user.is_authenticated:
        # Get runs from Parquet, sorted by mtime descending
        # Limiting to 1000 runs for performance; adjust as needed
        limit = 1000
        sorted_runs = Runs.query().order_by('mtime', ascending=False).limit(limit).all()
        return render_template("runs.html", title=source, runs=sorted_runs)
    else:
        return redirect(url_for("login"))


@app.route("/modules")
@login_required
def modules():
    if current_user.is_authenticated:
        modules = get_modules(folder=config_json.get("modules_dir", ""))
        return render_template("modules.html", modules=modules)
    else:
        return redirect(url_for("login"))


@app.route("/statistics")
@cached(ttl=30, key_prefix='statistics_data')
def statistics():
    # Vérifier si nous avons des données en cache
    cache_key = "statistics_page_data"
    cached_data = app_cache.get(cache_key)
    
    if cached_data:
        print(f"Using cached statistics page data (saved {time.time() - app_cache.timestamps.get(cache_key, 0):.3f} seconds ago)")
        return render_template(
            "statistics.html",
            repos=cached_data['repos'],
            activity_statistics=cached_data['activity_statistics'],
        )
    
    start_time = time.time()
    
    # Utiliser la fonction partagée pour récupérer les statistiques des runs
    run_stats = get_runs_statistics()
    
    # Définir repos avec les listes de noms
    repos = {
        "Input": run_stats['input_names'],
        "Repository": run_stats['repository_names'],
        "Archives": run_stats['archives_names']
    }
    
    # Utiliser la méthode optimisée et mise en cache pour les statistiques
    # Identique à celle utilisée dans la page d'accueil
    activity_statistics = activity_stats(use_dataframe=True)

    # Stocker les données en cache
    app_cache.set(cache_key, {
        'repos': repos,
        'activity_statistics': activity_statistics
    })
    
    # Log du temps d'exécution
    print(f"Statistics page data prepared in {time.time() - start_time:.3f} seconds")
    
    return render_template(
        "statistics.html",
        repos=repos,
        activity_statistics=activity_statistics,
    )


@app.route("/activity")
@login_required
def activity():
    # Pour l'activité, nous avons besoin de plus de runs, mais pas nécessairement tous
    limit = 1200  # Ajustez selon vos besoins et la taille typique de votre base
    
    # Récupérer seulement le nombre de runs dont nous avons besoin, triés par mtime
    sorted_runs = Runs.query().order_by('mtime', ascending=False).limit(limit).all()
    
    # Obtenir le nombre total de runs sans les charger tous
    total_runs = Runs.query().count()
    
    return render_template(
        "activity_parquet.html",
        runs=sorted_runs,
        runs_number=total_runs,
        limit=limit,
        runs_mode="cards",
    )


@app.route("/about")
def about():
    return render_template("about.html")


def populate():
    # atime = os.path.getatime("/tmp")
    # ctime = os.path.getctime("/tmp")
    # mtime = os.path.getmtime("/tmp")
    # print(f"atime={atime}")
    # print(f"ctime={ctime}")
    # print(f"mtime={mtime}")

    # struct_filter = {"DIAG": {}}
    folders_runs = config_json.get("folders_runs", {})
    folders_services = config_json.get("folders_services", {})
    struct_filter = config_json.get("struct_filter", {})

    # print("Input")
    runs_input = get_directories(
        root_dir=folders_runs.get("Input"), level=1, struct_filter={}
    )
    # get_runs_folder(folder=folders_runs.get("Input"), level=1)
    # print("Repository")
    runs_repository = get_directories(
        root_dir=folders_runs.get("Repository"),
        level=3,
        struct_filter=struct_filter,
    )
    # get_runs_folder(folder=folders_runs.get("Repository"), level=3)
    # print("Archives")
    runs_archives = get_directories(
        root_dir=folders_runs.get("Archives"), level=3, struct_filter=struct_filter
    )

    # api: STARK.z6rNIrvUrqU7.ID-d00a3a152268e4f8dec9f252a3000d5f29c8fbab-NAME-RUN_TEST.info json output
    # listener: ID-a569dc2c79a75b78f67025bc6360c489fb1a3b32-NAME-RUN_TEST_new.log

    # listener_files = find_most_recent_file(
    #     folder=folders_services.get("Listener"), pattern="ID-*-NAME-*.log"
    # )
    # listener_files = find_files(
    #     folder=folders_services.get("Listener"), pattern="*.log"
    # )
    # api_files_info = find_files(
    #     folder=folders_services.get("API"),
    #     pattern="STARK.*.ID-*-NAME-*.info",
    # )
    # api_files_json = find_files(
    #     folder=folders_services.get("API"),
    #     pattern="STARK.*.ID-*-NAME-*.json",
    # )
    # api_files_output = find_files(
    #     folder=folders_services.get("API"),
    #     pattern="STARK.*.ID-*-NAME-*.output",
    # )
    # print(f"listener_files={listener_files}")
    # print(f"api_files_info={api_files_info}")
    # print(f"api_files_json={api_files_json}")
    # print(f"api_files_output={api_files_output}")

    files_log = get_files_log(
        folders=folders_services,
        exts=["log", "info", "json", "output", "err"],
    )
    # print(f"files_log={files_log}")
    logs = {}
    for run_name in files_log:
        logs[run_name] = {}
        for log_source in files_log.get(run_name):
            if files_log.get(run_name).get(log_source).get("mtime", 0) > logs.get(
                run_name
            ).get("mtime", 0):
                logs[run_name] = files_log.get(run_name).get(log_source)
                # for item in files_log.get(run_name).get(log_source):
                #     print(f"{run_name} - {log_source} - {item}")
    # print(f"logs={logs}")

    # print(f"Input: {len(runs_input)}")
    # print(f"Input: {runs_input}")
    # print(f"Repository: {len(runs_repository)}")
    # print(f"Archives: {len(runs_archives)}")

    # runs_infos = {}
    # for run_name in runs_input:
    #     if run_name not in runs_infos:
    #         runs_infos[run_name] = {}
    #     print(f"run_name={run_name}")
    #     runs_infos[run_name]["input_path"] = runs_input.get(run_name).get("path", None)
    #     runs_infos[run_name]["input_mtime"] = runs_input.get(run_name).get("mtime", None)

    sources = {
        "input": runs_input,
        "repository": runs_repository,
        "archives": runs_archives,
        "analysis": logs,
    }

    runs_infos = {}
    for source in sources:
        runs_source = sources.get(source)
        for run_name in runs_source:
            if run_name not in runs_infos:
                runs_infos[run_name] = {}
            
            # Assurons-nous que les chemins et les mtime sont correctement définis
            if source in ["input", "repository", "archives"]:
                if "path" in runs_source.get(run_name):
                    runs_infos[run_name][f"{source}_path"] = runs_source.get(run_name).get("path")
                if "mtime" in runs_source.get(run_name):
                    runs_infos[run_name][f"{source}_mtime"] = runs_source.get(run_name).get("mtime")
                if "last_modified" in runs_source.get(run_name):
                    runs_infos[run_name][f"{source}_last_modified"] = runs_source.get(run_name).get("last_modified")
            
            # Pour d'autres éléments, gardons l'ancienne logique
            for item in runs_source.get(run_name):
                if item not in ["path", "mtime", "last_modified"] or source == "analysis":
                    runs_infos[run_name][f"{source}_{item}"] = runs_source.get(
                        run_name
                    ).get(item, None)

    # print(f"runs_infos={runs_infos}")
    for run_name in runs_infos:
        # print(f"run_name={run_name}")
        run_infos = runs_infos.get(run_name)
        # print(f"Run infos {run_infos}")
        run_check = Runs.query().filter_by(name=run_name).first()
        inserted = False

        if not run_check:
            # Insert run
            print(f"Run '{run_name}' insert...")
            run = Runs()
            run.name = run_name
            # Use Parquet save instead of db.session.add
            run.save()
            inserted = True
            run_check = Runs.query().filter_by(name=run_name).first()
            # db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
            # db.session.commit()

        # Run infos extra
        run_infos_extra = {}

        # Init
        updated = False

        # INPUT update
        if (inserted and run_infos.get("input_mtime", None)) or (
            run_infos.get("input_mtime", None)
            and run_check.input_mtime
            and run_infos.get("input_mtime", 0) > run_check.input_mtime
        ):

            # Updated
            updated = True

            # Find sampleSheet
            input_path = run_infos.get("input_path", None)
            if (
                input_path
                and os.path.isdir(input_path)
                and os.path.isfile(os.path.join(input_path, "SampleSheet.csv"))
            ):
                # run_infos_extra["input_samplesheet"] = os.path.join(
                #     input_path, "SampleSheet.csv"
                # )
                run_infos_extra["input_samplesheet"] = open(
                    str(os.path.join(input_path, "SampleSheet.csv")), "r"
                ).read()
            if (
                input_path
                and os.path.isdir(input_path)
                and os.path.isfile(os.path.join(input_path, "RTAComplete.txt"))
            ):
                # run_infos_extra["input_rtacomplete"] = os.path.join(
                #     input_path, "RTAComplete.txt"
                # )
                run_infos_extra["input_rtacomplete"] = open(
                    os.path.join(input_path, "RTAComplete.txt"), "r"
                ).read()

        # ANALYSIS update
        if (inserted and run_infos.get("analysis_mtime", None)) or (
            run_infos.get("analysis_mtime", None)
            and run_check.analysis_mtime
            and run_infos.get("analysis_mtime", 0) > run_check.analysis_mtime
        ):

            # Updated
            updated = True

            # analysis_path = run_infos.get("analysis_path", None)
            run_files_log = files_log.get(run_check.name, {})
            for run_file_log_type in run_files_log:
                run_infos_extra[f"analysis_{run_file_log_type}"] = open(
                    run_files_log.get(run_file_log_type).get("path"), "r"
                ).read()
                # run_infos_extra["analysis_api_info"] = open(
                #     os.path.join(repository_path, "STARKCopyComplete.txt"), "r"
                # ).read()

        # REPOSITORY update
        if (inserted and run_infos.get("repository_mtime", None)) or (
            run_infos.get("repository_mtime", None)
            and run_check.repository_mtime
            and run_infos.get("repository_mtime", 0) > run_check.repository_mtime
        ):

            # Updated
            updated = True

            # Repository path
            repository_path = run_infos.get("repository_path", None)

            # Group
            run_infos_extra["group"] = os.path.basename(
                os.path.dirname(os.path.dirname(repository_path))
            )

            # Project
            run_infos_extra["project"] = os.path.basename(
                os.path.dirname(repository_path)
            )

            # STARKComplete
            if (
                repository_path
                and os.path.isdir(repository_path)
                and os.path.isfile(
                    os.path.join(repository_path, "STARKCopyComplete.txt")
                )
            ):
                run_infos_extra["repository_starkcomplete"] = open(
                    os.path.join(repository_path, "STARKCopyComplete.txt"), "r"
                ).read()

            # Analysis log
            analysis_log = find_most_recent_file(
                folder=repository_path, pattern="STARK.*.analysis.log"
            )
            if (
                repository_path
                and os.path.isdir(repository_path)
                and analysis_log
                and os.path.isfile(analysis_log)
            ):
                run_infos_extra["repository_analysislog"] = zlib.compress(
                    open(analysis_log, "r").read().encode()
                )

            # Config
            config_log = find_most_recent_file(
                folder=repository_path, pattern="STARK.*.config"
            )
            if (
                repository_path
                and os.path.isdir(repository_path)
                and config_log
                and os.path.isfile(config_log)
            ):
                run_infos_extra["repository_config"] = open(config_log, "r").read()

        # ARCHIVES update
        if (inserted and run_infos.get("archives_mtime", None)) or (
            run_infos.get("archives_mtime", None)
            and run_check.archives_mtime
            and run_infos.get("archives_mtime", 0) > run_check.archives_mtime
        ):

            # Updated
            updated = True

            # Archives path
            archives_path = run_infos.get("archives_path", None)

            if (
                run_infos.get("archives_path", None)
                and "group" not in run_infos_extra
                and "project" not in run_infos_extra
            ):
                # Group
                run_infos_extra["group"] = os.path.basename(
                    os.path.dirname(os.path.dirname(run_infos.get("archives_path", "")))
                )

                # Project
                run_infos_extra["project"] = os.path.basename(
                    os.path.dirname(run_infos.get("archives_path", ""))
                )

            # STARKComplete
            if (
                archives_path
                and os.path.isdir(archives_path)
                and os.path.isfile(os.path.join(archives_path, "STARKCopyComplete.txt"))
            ):
                run_infos_extra["archives_starkcomplete"] = open(
                    os.path.join(archives_path, "STARKCopyComplete.txt"), "r"
                ).read()

            # Analysis log
            analysis_log = find_most_recent_file(
                folder=archives_path, pattern="STARK.*.analysis.log"
            )
            if (
                archives_path
                and os.path.isdir(archives_path)
                and analysis_log
                and os.path.isfile(analysis_log)
            ):
                run_infos_extra["archives_analysislog"] = zlib.compress(
                    open(analysis_log, "r").read().encode()
                )

            # Config
            config_log = find_most_recent_file(
                folder=archives_path, pattern="STARK.*.config"
            )
            if (
                archives_path
                and os.path.isdir(archives_path)
                and config_log
                and os.path.isfile(config_log)
            ):
                run_infos_extra["archives_config"] = open(config_log, "r").read()

            # db.session.commit()
        # else:
        #     print(f"Run '{run_name} no update needed")

        if run_infos_extra:
            print(f"Run '{run_name}' update...")
            # Use Parquet update instead of db.session.query...update
            run = Runs.query().filter_by(name=run_name).first()
            if run:
                for key, value in run_infos_extra.items():
                    setattr(run, key, value)
                run.save()
        # else:
        #     print(f"Run '{run_name} no update needed")

        if inserted or updated or run_infos_extra:
            # global mtime
            run_infos["mtime"] = max(
                run_check.input_mtime,
                run_check.analysis_mtime,
                run_check.repository_mtime,
                run_check.archives_mtime,
            )
            run_infos["mtime"] = max(
                run_infos.get("input_mtime", 0),
                run_infos.get("analysis_mtime", 0),
                run_infos.get("repository_mtime", 0),
                run_infos.get("archives_mtime", 0),
            )
            run_infos["last_modified"] = datetime.datetime.fromtimestamp(
                run_infos["mtime"]
            ).strftime("%Y-%m-%d %H:%M:%S")

            # Use Parquet update instead of db.session.query...update and commit
            run = Runs.query().filter_by(name=run_name).first()
            if run:
                for key, value in run_infos.items():
                    setattr(run, key, value)
                run.save()

            # print("")
            run_check = Runs.query().filter_by(name=run_name).first()
            # print(f"run_check={run_check.name}")
            print(f"Run '{run_name}' status...")
            run_status = run_status_calculation(run=run_check)
            # print(f"run_check2={run_check.name}")
            # print(f"run_status={run_status}")
            # Use Parquet update instead of db.session.query...update and commit
            run = Runs.query().filter_by(name=run_name).first()
            if run:
                for key, value in run_status.items():
                    setattr(run, key, value)
                run.save()

    # else:
    #     # Insert run
    #     print(f"Run '{run_name}' insert")

    #     run = Runs(name=run_name)
    #     db.session.add(run)
    #     db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
    
    # Rafraîchir les caches après les modifications de la base de données
    refresh_runs_cache()
    #     db.session.commit()


@cached(ttl=30, key_prefix='run_status')
def run_status_calculation(run) -> dict:
    """
    Calcule le statut d'un run à partir de ses attributs.
    Cette fonction est mise en cache pour améliorer les performances.
    
    Args:
        run: L'objet run à évaluer
        
    Returns:
        Dict contenant les statuts de séquençage, analyse, repository et archives
    """
    # primary
    # secondary
    # success
    # info
    # warning
    # danger

    # print(f"run={run.name}")
    status = {
        "status_sequencing": run.status_sequencing,
        "status_analysis": run.status_analysis,
        "status_repository": run.status_repository,
        "status_archives": run.status_archives,
    }

    # INPUT
    if run.input_mtime > 0:
        status["status_sequencing"] = "info"
    if run.input_samplesheet is None or not run.input_samplesheet:
        status["status_sequencing"] = "warning"
    if run.input_rtacomplete is not None:
        status["status_sequencing"] = "success"
    if not status["status_sequencing"]:
        status["status_sequencing"] = "secondary"

    # ANALYSIS
    if run.analysis_mtime > 0:
        status["status_analysis"] = "info"
    if run.analysis_api_json is not None:
        status["status_analysis"] = "info"
    # info : Exit status: died with exit code
    if hasattr(run, 'analysis_api_info') and run.analysis_api_info is not None:
        find_error = re.findall(
            r"Exit status. died with exit code", run.analysis_api_info
        )
        # print(find_error)
        if find_error:
            # print("found")
            status["status_analysis"] = "danger"
        else:
            status["status_analysis"] = "success"

    # REPOSITORY
    if status["status_analysis"] == "danger" and False:
        status["status_repository"] = status["status_analysis"]
    else:
        if run.repository_mtime > 0:
            status["status_repository"] = "info"
        if run.repository_starkcomplete is not None:
            status["status_repository"] = "success"
        if run.repository_analysislog is not None:
            # find_error = re.findall(rf"\*\*\*", run.repository_analysislog)
            find_error = re.findall(
                rf"\*\*\*", zlib.decompress(run.repository_analysislog).decode()
            )
            # zlib.decompress(a).decode()
            if find_error:
                status["status_repository"] = "danger"
        if not status["status_repository"]:
            status["status_repository"] = "secondary"

    # Adjust analysis status if repository ok
    if not status.get("status_analysis", None) and status.get(
        "status_repository", None
    ):
        status["status_analysis"] = status["status_repository"]

    # ARCHIVES
    if run.archives_mtime > 0:
        status["status_archives"] = "info"
    if run.archives_starkcomplete is not None:
        status["status_archives"] = "success"
    if run.archives_analysislog is not None:
        find_error = re.findall(
            rf"\*\*\*", zlib.decompress(run.archives_analysislog).decode()
        )
        if find_error:
            status["status_archives"] = "danger"
    if not status["status_archives"]:
        status["status_archives"] = "secondary"

    return status


from edith.cache import app_cache, cached

@cached(ttl=30, key_prefix='activity_stats')
def activity_stats(runs=None, use_dataframe=False) -> dict:
    """
    Calculate activity statistics either from a list of run objects or directly from Parquet data
    This function is cached to improve performance.
    
    Args:
        runs: Optional list of run objects. If None and use_dataframe is True, stats will be calculated directly from Parquet.
        use_dataframe: If True, calculate stats directly from Parquet dataframe for better performance
        
    Returns:
        Dictionary of activity statistics
    """
    # Check if we have this in cache
    cache_key = f"activity_stats:{use_dataframe}"
    cached_stats = app_cache.get(cache_key)
    if cached_stats:
        return cached_stats
        
    # Initialiser la structure des statistiques
    activity_statistics = {
        "Sequencing": {
            "secondary": 0,
            "info": 0,
            "warning": 0,
            "success": 0,
            "danger": 0,
        },
        "Analysis": {
            "secondary": 0,
            "info": 0,
            "warning": 0,
            "success": 0,
            "danger": 0,
        },
        "Repository": {
            "secondary": 0,
            "info": 0,
            "warning": 0,
            "success": 0,
            "danger": 0,
        },
        "Archives": {
            "secondary": 0,
            "info": 0,
            "warning": 0,
            "success": 0,
            "danger": 0,
        },
    }
    
    if use_dataframe:
        # Calcule les statistiques directement depuis les données Parquet
        # Cette méthode est beaucoup plus efficace pour les grands ensembles de données
        def count_status_values(df, column):
            # Compter les valeurs non-nulles de chaque statut
            counts = df[column].value_counts().to_dict()
            # Si des valeurs nulles, les compter comme "secondary"
            null_count = df[column].isna().sum()
            if null_count > 0:
                counts['secondary'] = counts.get('secondary', 0) + null_count
            # S'assurer que toutes les clés existent
            for key in ["secondary", "info", "warning", "success", "danger"]:
                if key not in counts:
                    counts[key] = 0
            return counts
        
        # Exécuter directement des requêtes sur le fichier Parquet pour calculer les statistiques
        df = pd.read_parquet(store._get_file_path('runs'))
        
        # Calculer les statistiques pour chaque étape
        for step in activity_statistics.keys():
            column = f"status_{step.lower()}"
            if column in df.columns:
                status_counts = count_status_values(df, column)
                activity_statistics[step].update(status_counts)
    else:
        # Méthode traditionnelle avec objets runs
        if runs:
            for run in runs:
                for step in activity_statistics:
                    status_attr = f"status_{step.lower()}"
                    if hasattr(run, status_attr):
                        status = getattr(run, status_attr)
                        if not status:
                            status = "secondary"
                        activity_statistics[step][status] += 1
    
    # Cache the result
    app_cache.set(cache_key, activity_statistics)
    return activity_statistics


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="EDITH",
        description="EDITH interface for STARK Analysis monitoring",
        epilog="",
    )
    parser.add_argument(
        "-p", "--populate", action="store_true", help="Populate database"
    )
    parser.add_argument(
        "-l",
        "--listener",
        action="store_true",
        help="Listener to populate database",
    )
    parser.add_argument(
        "-t",
        "--time_listener",
        type=int,
        default=10,
        help="Set time for listener (every 10 seconds by default)",
    )
    # parser.add_argument(
    #     "-c",
    #     "--config",
    #     type=argparse.FileType("r", encoding="UTF-8"),
    #     help="EDITH Config file",
    # )
    parser.add_argument("-i", "--ihm", action="store_true", help="Run IHM server")

    args = parser.parse_args()

    if not args.populate and not args.listener and not args.ihm:
        parser.print_help()
        exit()

    if args.populate:
        populate()

    if args.listener:
        while True:
            populate()
            time.sleep(args.time_listener)

    if args.ihm:

        Bootstrap(app)
        app.run(host='0.0.0.0', port=5001)
