locals {
  spec = templatefile("${path.module}/api-spec.yml", {
    LAMBDA_INVOCATION_URI = module.lambda_function.lambda_function_invoke_arn
  })
}

resource "aws_api_gateway_rest_api" "dt" {
  body = local.spec
  name = "${local.project_name}_api-prod"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "dt" {
  rest_api_id = aws_api_gateway_rest_api.dt.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.dt.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "stage" {
  deployment_id = aws_api_gateway_deployment.dt.id
  rest_api_id   = aws_api_gateway_rest_api.dt.id
  stage_name    = local.project_name
}

resource "aws_api_gateway_method_settings" "general_settings" {
  rest_api_id = aws_api_gateway_rest_api.dt.id
  stage_name  = aws_api_gateway_stage.stage.stage_name
  method_path = "*/*"

  settings {
    # Enable CloudWatch logging and metrics
    metrics_enabled    = true
    data_trace_enabled = true
    logging_level      = "INFO"

    # Limit the rate of calls to prevent abuse and unwanted charges
    throttling_rate_limit  = 100
    throttling_burst_limit = 50
  }
}