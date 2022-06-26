import boto3


def destroy_resource(arn):
    service = arn.split(":")[2]
    service_client = boto3.client(service)
    if service == "dynamodb":
        return destroy_dynamodb_table(service_client, arn)
    elif service == "s3":
        return destroy_s3_bucket(service_client, arn)
    elif service == "lambda":
        return destroy_lambda(service_client, arn)
    elif service == "logs":
        return destroy_log_group(service_client, arn)
    elif service == "apigateway" and "stages" not in arn:
        return destroy_apigateway(service_client, arn)
    return False


def destroy_lambda(service_client, arn):
    service_client.delete_function(FunctionName=arn)
    return True


def destroy_apigateway(service_client, arn):
    rest_api_id = arn.split('/')[-1]
    service_client.delete_rest_api(restApiId=rest_api_id)
    return True


def destroy_dynamodb_table(service_client, arn):
    table_name = arn.split("/")[-1]
    service_client.delete_table(TableName=table_name)
    return True


def destroy_s3_bucket(service_client, arn):
    bucket_name = arn.split(":")[-1]
    service_client.delete_bucket(Bucket=bucket_name)
    return True


def destroy_log_group(service_client, arn):
    name = arn.split(":")[-1]
    service_client.delete_log_group(logGroupName=name)
    return True


client = boto3.client("resourcegroupstaggingapi")
kwargs = {"TagFilters": [
    {"Key": "project", "Values": ["catan-tracker"]},
    #{"Key": "git_branch", "Values": ["feature/backend-lambda"]}
]}
results = []
while True:
    response = client.get_resources(**kwargs)
    results.extend(response["ResourceTagMappingList"])
    if not response["PaginationToken"]:
        break
    kwargs["PaginationToken"] = response["PaginationToken"]

for result in results:
    arn = result["ResourceARN"]
    print(f"Destroying {arn}...")
    if destroy_resource(arn):
        print(f"Destroyed {arn}")
    else:
        print(f"DID NOT DESTROY {arn}")