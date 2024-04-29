from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import boto3
import pathlib
import os
import time
import csv


app = Flask(__name__)
s3 = boto3.client("s3")

STATE_FILE = "state.txt"
HYPO_APP_LOAD_DURATION = int(os.environ.get("HYPO_APP_LOAD_DURATION", 15))  # seconds
DEFAULT_HICCUP_DURATION = int(os.environ.get("DEFAULT_HICCUP_DURATION", 5))  # seconds
S3_BUCKET = os.environ.get("S3_BUCKET")

if S3_BUCKET == None:
    raise EnvironmentError("S3_BUCKET is not set")

@app.route("/health")
def health_check():
    delay = int(request.args.get("delay", 0))
    time.sleep(delay)
    app_state = get_app_state()
    if app_state == "ok":
        return render_template("health.html", app_state=app_state, vars=os.environ.items())
    elif app_state == "loading":
        time.sleep(HYPO_APP_LOAD_DURATION)
        set_app_state("ok")

    return render_template("health.html", app_state=app_state, vars=os.environ.items()), 500


@app.route("/hiccup")
def hiccup_for():
    duration = int(request.args.get("for", DEFAULT_HICCUP_DURATION))
    set_app_state("hiccup")
    time.sleep(duration)
    set_app_state("ok")

    return "done"


@app.route("/", methods=["GET", "POST"])
def index():
    # The purpose of including this block is to imitate a failure like db connection error.
    app_state = get_app_state()
    if app_state not in (
        "ok",
        "loading",
    ):
        return render_template("error.html"), 500

    selected_file = request.args.get("select", "")
    contents = ""

    uploaded_file = None
    if request.method == "POST" and request.files["csv_file"].filename != "":
        uploaded_file = request.files["csv_file"]

        if uploaded_file and pathlib.Path(uploaded_file.filename).suffix == ".csv":
            uploaded_file.filename = secure_filename(uploaded_file.filename)
            process(
                uploaded_file,
            )
            selected_file = uploaded_file.filename

    if selected_file:
        object = s3.get_object(Bucket=S3_BUCKET, Key=selected_file)
        contents = filter(
            None, list(csv.reader(object["Body"].read().decode("utf-8").splitlines()))
        )

    objects = s3.list_objects_v2(
        Bucket=S3_BUCKET,
    )
    uploaded_file_list = (
        map(lambda obj: obj["Key"], objects["Contents"]) if objects["KeyCount"] > 0 else []
    )

    return render_template(
        "index.html", selected=selected_file, file_list=uploaded_file_list, contents=contents
    )


def process(file):
    s3.upload_fileobj(
        file,
        S3_BUCKET,
        file.filename,
        ExtraArgs={"ContentType": file.content_type},
    )


def get_app_state():
    return pathlib.Path("state.txt").read_text()


def set_app_state(state):
    pathlib.Path("state.txt").write_text(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
