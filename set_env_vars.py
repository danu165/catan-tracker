"""
This file is not for the application. It is used to load environment variables for local development
"""

import json
import os
import subprocess
from pathlib import Path

import boto3


def get_git_branch(path=None):
    if path is None:
        path = os.path.curdir
    command = "git rev-parse --abbrev-ref HEAD".split()
    branch = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=path).stdout.read()
    return branch.strip().decode("utf-8")


def main():
    # Get terraform state for current branch
    ssm = boto3.client("ssm")
    s3 = boto3.client("s3")
    bucket = ssm.get_parameter(Name="/tf_state/bucket_name")["Parameter"]["Value"]
    git_branch = get_git_branch()
    project_path = f"{Path(__file__).parent.absolute()}{os.sep}"
    project_name = Path(project_path).name
    state_s3_key = f"{project_name}/prod/state.json"
    print(f"Getting state {state_s3_key}")
    obj = s3.get_object(Bucket=bucket, Key=state_s3_key)
    tf_state = json.loads(obj["Body"].read().decode())

    # Set env
    os.environ["CONFIG_BUCKET"] = tf_state["outputs"]["config_bucket_name"]["value"]
    os.environ["MESSAGES_KEY"] = tf_state["outputs"]["messages_key"]["value"]
    os.environ["ENV"] = "prod" if git_branch == "main" else "feature"


if __name__ == "__main__":
    main()