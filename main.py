import argparse
import datetime
import os
import re
import sqlite3
import time
from flask import Flask, render_template, request, url_for, redirect, jsonify

# from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import load_only
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from flask_bootstrap import Bootstrap
from edith.runs import (
    find_files,
    find_most_recent_file,
    get_directories,
    get_files_log,
)  # , get_runs  # , get_runs_folder
from edith.modules import get_modules
from config.config import folders_runs, modules_dir, folders_services

# from objects.models import Users, Groups

# Bootstrap https://bootswatch.com/lux/


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "abc"
# app.config["ADMIN"] = "admin"

login_manager = LoginManager()
login_manager.init_app(app)

# # enable CORS
# CORS(app, resources={r"/*": {"origins": "*"}})

db = SQLAlchemy()


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    is_admin = db.Column(db.Boolean(), nullable=True)
    groups = db.Column(db.String(250), nullable=True)

    def update_profile(self, infos_get: dict):
        if infos_get:
            password = infos_get.get("password")
            if password == self.password:
                infos_update = {}
                self.groups = infos_get.get("groups")
                new_password1 = infos_get.get("new_password1")
                new_password2 = infos_get.get("new_password2")
                if new_password1 and new_password2:
                    if new_password1 == new_password2:
                        new_password = new_password1
                        infos_update["password"] = new_password
                        self.password = password
                    else:
                        return {
                            "error": f"User '{self.username}' not updated (wrong new password)!"
                        }
                if infos_update:
                    db.session.query(Users).filter(Users.id == self.id).update(
                        infos_update
                    )
                    db.session.commit()
                    return {"success": f"User '{self.username}' updated!"}
                else:
                    return {"info": f"User '{self.username}' not updated (no need)!"}
            else:
                return {
                    "error": f"User '{self.username}' not updated (wrong password)!"
                }
        else:
            return {"info": f"User '{self.username}' not updated (no need)!"}


class Groups(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(250), unique=True, nullable=False)


class Runs(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    last_modified = db.Column(db.String(100), unique=False, nullable=True)
    input_path = db.Column(db.String(500), unique=False, nullable=True)
    input_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    input_last_modified = db.Column(db.String(100), unique=False, nullable=True)
    input_samplesheet = db.Column(db.Text, unique=False, nullable=True)
    input_rtacomplete = db.Column(db.Text, unique=False, nullable=True)
    repository_path = db.Column(db.String(500), unique=False, nullable=True)
    repository_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    repository_last_modified = db.Column(db.String(100), unique=False, nullable=True)
    repository_starkcomplete = db.Column(db.Text, unique=False, nullable=True)
    repository_analysislog = db.Column(db.Text, unique=False, nullable=True)
    repository_config = db.Column(db.Text, unique=False, nullable=True)
    archives_path = db.Column(db.String(500), unique=False, nullable=True)
    archives_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    archives_last_modified = db.Column(db.String(100), unique=False, nullable=True)
    archives_starkcomplete = db.Column(db.Text, unique=False, nullable=True)
    archives_analysislog = db.Column(db.Text, unique=False, nullable=True)
    archives_config = db.Column(db.Text, unique=False, nullable=True)
    analysis_path = db.Column(db.String(500), unique=False, nullable=True)
    analysis_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    analysis_last_modified = db.Column(db.String(100), unique=False, nullable=True)
    analysis_listener_log = db.Column(db.Text, unique=False, nullable=True)
    analysis_listener_json = db.Column(db.Text, unique=False, nullable=True)
    analysis_listener_info = db.Column(db.Text, unique=False, nullable=True)
    analysis_listener_output = db.Column(db.Text, unique=False, nullable=True)
    analysis_listener_err = db.Column(db.Text, unique=False, nullable=True)
    analysis_api_log = db.Column(db.Text, unique=False, nullable=True)
    analysis_api_json = db.Column(db.Text, unique=False, nullable=True)
    analysis_api_info = db.Column(db.Text, unique=False, nullable=True)
    analysis_api_output = db.Column(db.Text, unique=False, nullable=True)
    analysis_api_err = db.Column(db.Text, unique=False, nullable=True)
    group = db.Column(db.String(50), unique=False, nullable=True)
    project = db.Column(db.String(50), unique=False, nullable=True)
    status_sequencing = db.Column(db.String(50), unique=False, nullable=True)
    status_analysis = db.Column(db.String(50), unique=False, nullable=True)
    status_repository = db.Column(db.String(50), unique=False, nullable=True)
    status_archives = db.Column(db.String(50), unique=False, nullable=True)
    samples = db.Column(db.Integer(), unique=False, nullable=True, default=0)


db.init_app(app)

with app.app_context():
    db.create_all()

app.app_context().push()

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
    return Users.query.get(user_id)


# sanity check route
@app.route("/ping", methods=["GET"])
def ping_pong():
    return jsonify("pong!")


@app.route("/test")
def test():
    # cur = get_db().cursor()
    return render_template("main.html")


def populate():
    # atime = os.path.getatime("/tmp")
    # ctime = os.path.getctime("/tmp")
    # mtime = os.path.getmtime("/tmp")
    # print(f"atime={atime}")
    # print(f"ctime={ctime}")
    # print(f"mtime={mtime}")

    # struct_filter = {"DIAG": {}}
    struct_filter = {}

    # print("Input")
    runs_input = get_directories(
        root_dir=folders_runs.get("Input"), level=1, struct_filter={}
    )
    # get_runs_folder(folder=folders_runs.get("Input"), level=1)
    # print("Repository")
    runs_repository = get_directories(
        root_dir=folders_runs.get("Repository"), level=3, struct_filter=struct_filter
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
            # print(f"run_name={run_name}")
            for item in runs_source.get(run_name):
                runs_infos[run_name][f"{source}_{item}"] = runs_source.get(
                    run_name
                ).get(item, None)
            # runs_infos[run_name][f"{source}_path"] = runs_source.get(run_name).get(
            #     "path", None
            # )
            # runs_infos[run_name][f"{source}_mtime"] = runs_source.get(run_name).get(
            #     "mtime", None
            # )

    # print(f"runs_infos={runs_infos}")
    for run_name in runs_infos:
        # print(f"run_name={run_name}")
        run_infos = runs_infos.get(run_name)
        # print(f"Run infos {run_infos}")
        run_check = Runs.query.filter_by(name=run_name).first()
        inserted = False

        if not run_check:
            # Insert run
            print(f"Run '{run_name}' insert...")
            run = Runs(name=run_name)
            db.session.add(run)
            inserted = True
            run_check = Runs.query.filter_by(name=run_name).first()
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

        # ANALAYSIS update
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
                run_infos_extra["repository_analysislog"] = open(
                    analysis_log, "r"
                ).read()

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
                run_infos_extra["archives_analysislog"] = open(analysis_log, "r").read()

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
            db.session.query(Runs).filter(Runs.name == run_name).update(run_infos_extra)
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

            db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
            db.session.commit()

            # print("")
            run_check = Runs.query.filter_by(name=run_name).first()
            # print(f"run_check={run_check.name}")
            print(f"Run '{run_name}' status...")
            run_status = run_status_calculation(run=run_check)
            # print(f"run_check2={run_check.name}")
            # print(f"run_status={run_status}")
            db.session.query(Runs).filter(Runs.name == run_name).update(run_status)
            db.session.commit()

    # else:
    #     # Insert run
    #     print(f"Run '{run_name}' insert")

    #     run = Runs(name=run_name)
    #     db.session.add(run)
    #     db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
    #     db.session.commit()


def run_status_calculation(run) -> dict:

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
    # info : Exit status: died with exit code
    if run.analysis_api_info is not None:
        # print(f"{run.name}")
        find_error = re.findall(
            r"Exit status. died with exit code", run.analysis_api_info
        )
        # print(find_error)
        if find_error:
            # print("found")
            status["status_analysis"] = "danger"
    # if not status["status_analysis"]:
    #     status["status_analysis"] = "secondary"
    # print(status["status_analysis"])

    # REPOSITORY
    if status["status_analysis"] == "danger":
        status["status_repository"] = status["status_analysis"]
    else:
        if run.repository_mtime > 0:
            status["status_repository"] = "info"
        if run.repository_starkcomplete is not None:
            status["status_repository"] = "success"
        if run.repository_analysislog is not None:
            find_error = re.findall(rf"\*\*\*", run.repository_analysislog)
            if find_error:
                status["status_repository"] = "danger"
        if not status["status_repository"]:
            status["status_repository"] = "secondary"

    # ARCHIVES
    if run.archives_mtime > 0:
        status["status_archives"] = "info"
    if run.archives_starkcomplete is not None:
        status["status_archives"] = "success"
    if run.archives_analysislog is not None:
        find_error = re.findall(rf"\*\*\*", run.archives_analysislog)
        if find_error:
            status["status_archives"] = "danger"
    if not status["status_archives"]:
        status["status_archives"] = "secondary"

    return status


def activity_stats(runs: dict) -> dict:
    """ """

    # status_map = {
    #     "secondary": "unknown",
    #     "info": "waiting",
    #     "warning": "warning",
    #     "success": "success",
    #     "danger": "error",
    # }
    activity_statistics = {
        "Sequencing": {
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
    for run in runs:
        for step in activity_statistics:
            # val = getattr(run, f"status_{step}")
            # print(val)
            status = getattr(run, f"status_{step.lower()}")
            if not status:
                status = "secondary"
            activity_statistics[step][status] += 1

    return activity_statistics


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        user = Users.query.filter_by(id=current_user.id).first()
        result = user.update_profile(dict(request.form))
    else:
        result = {}

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
    user = Users.query.filter_by(id=current_user.id).first()
    if user.is_admin:
        populate()
        return render_template("admin.html", success="Populate OK")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # All users
        all_users = Users.query.order_by(Users.username).all()

        # Check admin
        if len(all_users):
            is_admin = False
        else:
            is_admin = True

        # Check username
        username = request.form.get("username")
        user_check = Users.query.filter_by(username=username).first()

        # Create user
        if user_check:
            return render_template(
                "sign_up.html",
                error=f"User '{username}' already exists. Choose another username.",
                username=username,
            )
        else:
            user = Users(
                username=request.form.get("username"),
                password=request.form.get("password"),
                is_admin=is_admin,
                groups="",
            )
            db.session.add(user)
            db.session.commit()
        return render_template("login.html", success=f"User '{username}' registered!")

    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    warning = None
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Users.query.filter_by(username=username).first()
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
        all_users = Users.query.order_by(Users.username).all()
        return render_template("admin.html", users=all_users)
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    fields = [
        "name",
        "mtime",
        "last_modified",
        "project",
        "group",
        "status_sequencing",
        "status_analysis",
        "status_repository",
        "status_archives",
    ]
    class_fields = [getattr(Runs, f) for f in fields]
    all_runs = Runs.query.with_entities(*class_fields).order_by(Runs.mtime).all()
    all_runs.reverse()

    repos = {
        "Input": Runs.query.filter(Runs.input_path != None)
        .with_entities(Runs.name)
        .all(),
        "Repository": Runs.query.filter(Runs.repository_path != None)
        .with_entities(Runs.name)
        .all(),
        "Archives": Runs.query.filter(Runs.archives_path != None)
        .with_entities(Runs.name)
        .all(),
    }
    all_runs_names = Runs.query.with_entities(Runs.name).all()

    activity_statistics = activity_stats(all_runs)

    modules = get_modules(folder=modules_dir)
    limit = 12
    return render_template(
        "main.html",
        runs=all_runs[:limit],
        all_runs_names=all_runs_names,
        runs_number=len(all_runs),
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
        fields = [
            "name",
            "mtime",
            "last_modified",
            "project",
            "group",
            "status_sequencing",
            "status_analysis",
            "status_repository",
            "status_archives",
        ]
        class_fields = [getattr(Runs, f) for f in fields]
        all_runs = Runs.query.with_entities(*class_fields).order_by(Runs.mtime).all()
        all_runs.reverse()
        return render_template("runs.html", title=source, runs=all_runs)
    else:
        return redirect(url_for("login"))


@app.route("/modules")
@login_required
def modules():
    if current_user.is_authenticated:
        modules = get_modules(folder=modules_dir)
        return render_template("modules.html", modules=modules)
    else:
        return redirect(url_for("login"))


@app.route("/statistics")
def statistics():
    fields = [
        "name",
        "mtime",
        "last_modified",
        "project",
        "group",
        "status_sequencing",
        "status_analysis",
        "status_repository",
        "status_archives",
    ]
    class_fields = [getattr(Runs, f) for f in fields]
    all_runs = Runs.query.with_entities(*class_fields).order_by(Runs.mtime).all()
    all_runs.reverse()

    repos = {
        "Input": Runs.query.filter(Runs.input_path != None)
        .with_entities(Runs.name)
        .all(),
        "Repository": Runs.query.filter(Runs.repository_path != None)
        .with_entities(Runs.name)
        .all(),
        "Archives": Runs.query.filter(Runs.archives_path != None)
        .with_entities(Runs.name)
        .all(),
    }

    activity_statistics = activity_stats(all_runs)

    return render_template(
        "statistics.html",
        repos=repos,
        activity_statistics=activity_statistics,
    )


@app.route("/activity")
@login_required
def activity():
    fields = [
        "name",
        "mtime",
        "last_modified",
        "project",
        "group",
        "status_sequencing",
        "status_analysis",
        "status_repository",
        "status_archives",
    ]
    class_fields = [getattr(Runs, f) for f in fields]
    all_runs = Runs.query.with_entities(*class_fields).order_by(Runs.mtime).all()
    all_runs.reverse()

    limit = 1200
    return render_template(
        "activity.html",
        runs=all_runs[:limit],
        runs_number=len(all_runs),
        limit=limit,
        runs_mode="cards",
    )


@app.route("/about")
def about():
    return render_template("about.html")


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
    parser.add_argument("-i", "--ihm", action="store_true", help="Run IHM server")

    args = parser.parse_args()
    # print(args.populate, args.listener, args.ihm)

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
        app.run()
