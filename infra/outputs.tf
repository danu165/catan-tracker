output "api_endpoint" {
  value = local.api_endpoint
}

output "git_branch" {
  value = local.git_branch
}

output "branch_hash" {
  value = local.branch_hash
}

output "lambda_role_arn" {
  value = module.lambda_function["sms_interface"].lambda_role_arn
}