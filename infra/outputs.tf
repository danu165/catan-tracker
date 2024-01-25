output "git_branch" {
  value = local.git_branch
}

output "branch_hash" {
  value = local.branch_hash
}

output "lambda_role_arn" {
  value = module.lambda_function.lambda_role_arn
}

output "config_bucket_name" {
  value = aws_s3_bucket.b.bucket
}

output "api_endpoint" {
  value = local.api_endpoint
}

output "messages_key" {
  value = local.messages_key
}