#!/usr/bin/env bash

# Variable setup
set -e -x
bucket=$(aws ssm get-parameter --name "/tf_state/bucket_name" --query 'Parameter.Value' --output text)
gitBranch=$(git rev-parse --abbrev-ref HEAD)
projectName=${PWD##*/}
stateS3Key="${projectName}/${gitBranch}/state.json"
awsRegion="${AWS_DEFAULT_REGION:-us-west-2}"

# Zip python dependencies in docker container for Lambda Layer
docker run -it -d --name dummypython python:3.9-slim /bin/bash
docker cp Pipfile dummypython:/
docker cp Pipfile.lock dummypython:/
cat <<EOM | docker exec -i dummypython /bin/bash
export PIPENV_VENV_IN_PROJECT=1
apt-get update && apt-get install -y zip
pip install pipenv
pipenv install
mkdir python && cp -r .venv/lib python/
zip -mrqX lambda_layer.zip python -x *__pycache__* .*
EOM
docker cp dummypython:lambda_layer.zip infra/lambda_layer.zip
docker rm -f dummypython

# Build AWS infra
cd infra
terraform --version
terraform init \
-backend-config="bucket=${bucket}" \
-backend-config="key=${stateS3Key}" \
-backend-config="region=${awsRegion}"
terraform apply -auto-approve