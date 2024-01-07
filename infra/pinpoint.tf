# create a phone pool
# create a configuration set

resource "aws_pinpoint_app" "app" {
  count = local.is_main ? 1 : 0
  name  = local.project_name
}

resource "aws_pinpoint_sms_channel" "sms" {
  count          = local.is_main ? 1 : 0
  application_id = aws_pinpoint_app.app[0].application_id
}

# After setting this up, I used the Pinpoint UI to request a toll-free number