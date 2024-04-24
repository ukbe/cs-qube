from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import boto3
import pathlib
import os
import csv


app = Flask(__name__)
s3 = boto3.client("s3")


def process(file):
    s3.upload_fileobj(
        file,
        os.environ.get("S3_BUCKET"),
        file.filename,
        ExtraArgs={"ContentType": file.content_type},
    )


@app.route("/", methods=["GET", "POST"])
def index():
    selected = request.args.get("select", "")
    contents = ""

    file = None
    if request.method == "POST" and request.files["csv_file"].filename != "":
        file = request.files["csv_file"]

        if file and pathlib.Path(file.filename).suffix == ".csv":
            file.filename = secure_filename(file.filename)
            process(
                file,
            )
            selected = file.filename

    if selected:
        object = s3.get_object(Bucket=os.environ.get("S3_BUCKET"), Key=selected)
        contents = filter(
            None, list(csv.reader(object["Body"].read().decode("utf-8").splitlines()))
        )

    objects = s3.list_objects_v2(
        Bucket=os.environ.get("S3_BUCKET"),
    )
    file_list = map(lambda obj: obj["Key"], objects["Contents"]) if objects["KeyCount"] > 0 else []
    return render_template("index.html", selected=selected, file_list=file_list, contents=contents)
