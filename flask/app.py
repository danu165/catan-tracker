import os
import sys
import traceback
from pathlib import Path

from flask import Flask, abort, make_response, render_template, request

PROJECT_PATH = f"{Path(__file__).parent.parent.absolute()}{os.sep}"
sys.path.insert(1, PROJECT_PATH)

import set_env_vars
from src.ui_interface.lambda_function import lambda_handler

app = Flask(__name__, static_folder=f"{PROJECT_PATH}frontend")


def format_event(req):
    headers = {k: v for k, v in req.headers.items()}
    headers["X-Forwarded-Proto"] = "http"
    event = {
        "resource": req.path,
        "path": req.path,
        "httpMethod": req.method,
        "headers": headers,
        "queryStringParameters": req.args,
        "requestContext": {
            "resourcePath": req.path,
            "httpMethod": req.method,
            "path": req.path,
            "stage": "",
            "domainName": req.host,
        },
        "body": req.data.decode(),
    }
    return event


@app.route("/", methods=["GET"])
@app.route("/send", methods=["POST"])
@app.route("/login", methods=["POST"])
def forward_request():
    set_env_vars.main()
    event = format_event(request)
    handler_response = lambda_handler(event, None)
    response = make_response(handler_response["body"])
    try:
        return response
    except Exception:
        abort(handler_response["statusCode"])


@app.errorhandler(Exception)
def all_errors(e: Exception):
    try:
        status_code = e.status_code
    except Exception:
        status_code = 500
    return render_template("error.html", message=traceback.format_exc()), status_code