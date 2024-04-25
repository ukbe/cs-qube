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


@app.route("/health")
def health_check():
    delay = int(request.args.get("delay", 0))
    time.sleep(delay)
    app_state = get_app_state()
    if app_state == "ok":
        return render_template("env.html", state=app_state, vars=os.environ.items())

    return render_template("env.html", state=app_state, vars=os.environ.items()), 500


@app.route("/hiccup")
def hiccup_for():
    duration = int(request.args.get("for", 5))
    set_app_state("down")
    time.sleep(duration)
    set_app_state("ok")

    return "done"


@app.route("/", methods=["GET", "POST"])
def index():
    # This block is to imitate 500 on startup, so we know app is working as expected during demo. Not for production
    app_state = get_app_state()
    if app_state != "ok":
        return render_template("loading.html"), 500

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
        object = s3.get_object(Bucket=os.environ.get("S3_BUCKET"), Key=selected_file)
        contents = filter(
            None, list(csv.reader(object["Body"].read().decode("utf-8").splitlines()))
        )

    objects = s3.list_objects_v2(
        Bucket=os.environ.get("S3_BUCKET"),
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
        os.environ.get("S3_BUCKET"),
        file.filename,
        ExtraArgs={"ContentType": file.content_type},
    )


def get_app_state():
    return pathlib.Path("state.txt").read_text()


def set_app_state(state):
    pathlib.Path("state.txt").write_text(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
