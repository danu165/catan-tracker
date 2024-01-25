locals {
  lambdas = ["sms_interface"]
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename         = "lambda_layer.zip"
  layer_name       = "${local.project_name}_layer-prod"
  source_code_hash = filebase64sha256("lambda_layer.zip")

  compatible_runtimes = ["python3.9"]
}


module "lambda_function" {
  source   = "terraform-aws-modules/lambda/aws"
  version  = "v6.5.0"

  function_name = "${local.project_name}-ui_interface-prod"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  publish       = true
  timeout       = 60
  memory_size   = 512

  source_path = "../src/ui_interface"
  role_name   = "${local.project_name}-sms_interface-prod"

  allowed_triggers = {
    ApiGW = {
      principal  = "apigateway.amazonaws.com"
      source_arn = "${aws_api_gateway_rest_api.dt.execution_arn}/*/*"
    }
  }

  environment_variables = {
    CONFIG_BUCKET  = aws_s3_bucket.b.bucket
    MESSAGES_KEY   = local.messages_key
  }

  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.frontend_permissions.json

  layers = [aws_lambda_layer_version.lambda_layer.arn]
}

#######################################################
# Permissions
#######################################################

data "aws_iam_policy_document" "frontend_permissions" {
  statement {
    sid = "Logs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }

  statement {
    sid = "S3"
    actions = [
      "s3:GetObject*",
      "s3:PutObject*",
    ]
    resources = [
      aws_s3_bucket.b.arn,
      "${aws_s3_bucket.b.arn}/*",
    ]
  }

}

# TODO:
# Cognito or something in front of API gateway