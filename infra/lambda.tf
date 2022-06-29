locals {
  lambdas = ["sms_interface"]
}

resource "aws_lambda_layer_version" "lambda_layer" {
  filename         = "lambda_layer.zip"
  layer_name       = "${local.project_name}_layer-${local.branch_hash}"
  source_code_hash = filebase64sha256("lambda_layer.zip")

  compatible_runtimes = ["python3.9"]
}

module "lambda_function" {
  for_each = toset(local.lambdas)
  source   = "terraform-aws-modules/lambda/aws"
  version  = "v3.3.1"

  function_name = "${local.project_name}-${each.value}-${local.branch_hash}"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  publish       = true
  timeout       = 60
  memory_size   = 512

  source_path = "../src/${each.value}"
  role_name   = "${local.project_name}-${each.value}-${local.branch_hash}"

  allowed_triggers = {
    ApiGw = {
      principal  = "apigateway.amazonaws.com"
      source_arn = "${aws_api_gateway_rest_api.dt.execution_arn}/*/*"
    }
  }

  layers = [aws_lambda_layer_version.lambda_layer.arn]
}