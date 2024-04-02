import argparse
import os
import sqlite3
import time
from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
from flask_bootstrap import Bootstrap
from edith.runs import get_directories, get_runs  # , get_runs_folder
from edith.modules import get_modules

# from objects.models import Users, Groups

# Bootstrap https://bootswatch.com/lux/


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = "abc"
# app.config["ADMIN"] = "admin"

login_manager = LoginManager()
login_manager.init_app(app)

# enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

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
    archives_path = db.Column(db.String(500), unique=False, nullable=True)
    archives_mtime = db.Column(db.Float, unique=False, nullable=True, default=0)
    archives_last_modified = db.Column(db.String(100), unique=False, nullable=True)
    archives_starkcomplete = db.Column(db.Text, unique=False, nullable=True)
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


# Config
folders_runs = {
    "Input": "/Users/lebechea/STARK/input/runs",
    "Repository": "/Users/lebechea/STARK/output/repository",
    "Archives": "/Users/lebechea/STARK/output/archives",
}
modules_dir = "/Users/lebechea/STARK/services"


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

    print("Input")
    runs_input = get_directories(root_dir=folders_runs.get("Input"), level=1)
    # get_runs_folder(folder=folders_runs.get("Input"), level=1)
    print("Repository")
    runs_repository = get_directories(root_dir=folders_runs.get("Repository"), level=3)
    # get_runs_folder(folder=folders_runs.get("Repository"), level=3)
    print("Archives")
    runs_archives = get_directories(root_dir=folders_runs.get("Archives"), level=3)

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
    }
    runs_infos = {}
    for source in sources:
        runs_source = sources.get(source)
        for run_name in runs_source:
            if run_name not in runs_infos:
                runs_infos[run_name] = {}
            print(f"run_name={run_name}")
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

    print(f"runs_infos={runs_infos}")
    for run_name in runs_infos:
        print(f"run_name={run_name}")
        run_infos = runs_infos.get(run_name)
        print(f"Run infos {run_infos}")
        run_check = Runs.query.filter_by(name=run_name).first()
        inserted = False
        if not run_check:
            # Insert run
            print(f"Run '{run_name}' insert")

            run = Runs(name=run_name)
            db.session.add(run)
            inserted = True
            run_check = Runs.query.filter_by(name=run_name).first()
            # db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
            # db.session.commit()

        # Update run
        print(f"Run '{run_name} update")
        run_infos_extra = {}
        if inserted or (
            run_infos.get("input_mtime", None)
            and run_check.input_mtime
            and run_infos.get("input_mtime", 0) > run_check.input_mtime
        ):
            # Find sampleSheet
            input_path = run_infos.get("input_path", None)
            if (
                input_path
                and os.path.isdir(input_path)
                and os.path.isfile(os.path.join(input_path, "SampleSheet.csv"))
            ):
                run_infos_extra["input_samplesheet"] = os.path.join(
                    input_path, "SampleSheet.csv"
                )
            if (
                input_path
                and os.path.isdir(input_path)
                and os.path.isfile(os.path.join(input_path, "RTAComplete.txt"))
            ):
                run_infos_extra["input_rtacomplete"] = os.path.join(
                    input_path, "RTAComplete.txt"
                )

        if inserted or (
            run_infos.get("repository_mtime", None)
            and run_check.repository_mtime
            and run_infos.get("repository_mtime", 0) > run_check.repository_mtime
        ):
            run_infos_extra["group"] = os.path.basename(
                os.path.dirname(os.path.dirname(run_infos.get("repository_path", "")))
            )
            run_infos_extra["project"] = os.path.basename(
                os.path.dirname(run_infos.get("repository_path", ""))
            )
            # run_repository_infos = {
            #     "group": os.path.basename(
            #         os.path.dirname(
            #             os.path.dirname(run_infos.get("repository_path", ""))
            #         )
            #     ),
            #     "project": os.path.basename(
            #         os.path.dirname(run_infos.get("repository_path", ""))
            #     ),
            # }
            print(f"run_infos_extra={run_infos_extra}")
            # exit()

            # db.session.commit()
        else:
            print(f"Run '{run_name} no update needed")

        if run_infos_extra:
            db.session.query(Runs).filter(Runs.name == run_name).update(run_infos_extra)

        db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
        db.session.commit()
    # else:
    #     # Insert run
    #     print(f"Run '{run_name}' insert")

    #     run = Runs(name=run_name)
    #     db.session.add(run)
    #     db.session.query(Runs).filter(Runs.name == run_name).update(run_infos)
    #     db.session.commit()


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

    # return render_template(
    #     "profile.html",
    #     success=result.get("success"),
    #     info=result.get("info"),
    #     warning=result.get("warning"),
    #     error=result.get("error"),
    # )


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
        # return redirect(url_for("login"), success=f"User '{username}' registered!")
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
    # source = "Repository"
    # folder = folders_runs.get(source, None)
    # runs = get_runs(folder=folder, type=source)
    # runs_input = get_runs(folder=folders_runs.get("Input", None), type="Input")
    # runs_repository = get_runs(
    #     folder=folders_runs.get("Repository", None), type="Repository"
    # )
    # runs_archives = get_runs(folder=folders_runs.get("Archives", None), type="Archives")
    # runs = (
    #     list(runs_input.keys())
    #     + list(runs_repository.keys())
    #     + list(runs_archives.keys())
    # )
    # runs_grouped = {
    #     "Input": runs_input,
    #     "Repository": runs_repository,
    #     "Archives": runs_archives,
    # }
    # runs_counts = {
    #     "Input": len(runs_input),
    #     "Repository": len(runs_repository),
    #     "Archives": len(runs_archives),
    # }
    all_runs = Runs.query.order_by(
        Runs.input_mtime,
        Runs.repository_mtime,
        Runs.archives_mtime,
    ).all()
    # print(all_runs)
    all_runs.reverse()
    # print(all_runs)
    repos = {
        "Input": Runs.query.filter(Runs.input_path != None).all(),
        "Repository": Runs.query.filter(Runs.repository_path != None).all(),
        "Archives": Runs.query.filter(Runs.archives_path != None).all(),
    }

    modules = get_modules(folder=modules_dir)
    return render_template(
        "main.html",
        runs=all_runs,
        runs_number=len(all_runs),
        limit=8,
        modules=modules,
        repos=repos,
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
        folder = folders_runs.get(source, None)
        runs = get_runs(folder=folder, type=source)
        return render_template("runs.html", title=source, runs=runs)
    else:
        return redirect(url_for("login"))


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
    print(args.populate, args.listener, args.ihm)

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
