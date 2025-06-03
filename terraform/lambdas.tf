######################################
## File creation
######################################
data "archive_file" "app_v1_lambda_file" {
  type = "zip"

  source_dir  = "../${path.module}/app"
  output_path = "../${path.module}/terraform/files/app.zip"
}

resource "aws_s3_object" "app_v1_s3_object" {
  bucket = aws_s3_bucket.app_v1_bucket.id

  key    = "app.zip"
  source = data.archive_file.app_v1_lambda_file.output_path

  etag = filemd5(data.archive_file.app_v1_lambda_file.output_path)
}

######################################
## Lambda creation (for each)
######################################
resource "aws_lambda_function" "app_v1_lambda_main" {
  for_each = var.lambdas

  function_name = each.value.name

  s3_bucket = aws_s3_bucket.app_v1_bucket.id
  s3_key    = aws_s3_object.app_v1_s3_object.key

  runtime = "python3.12"
  handler = each.value.handler

  source_code_hash = data.archive_file.app_v1_lambda_file.output_base64sha256

  role = aws_iam_role.app_v1_lambda_role.arn

  timeout = var.lambda_timeout

  environment {
    variables = {
      RETENTION_DAYS        = var.retention,
      AWS_DYNAMO_TEMP_TABLE = aws_dynamodb_table.app_v1_temperature.name
    }
  }

}

resource "aws_lambda_permission" "app_v1_api_gw_permission" {
  for_each = var.lambdas

  statement_id  = "AllowExecutionFromAPIGateway-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app_v1_lambda_main[each.key].function_name
  principal     = "apigateway.amazonaws.com"

  # Debe usar el ARN del REST API (no HTTP API) con stage 'prod'
  source_arn = "${aws_api_gateway_rest_api.app_v1_rest_api.execution_arn}/*/*"
}

##############################
# LAMBDA LOGS
##############################
resource "aws_cloudwatch_log_group" "iot_lambda_main" {
  for_each = var.lambdas
  name     = "/aws/lambda/${aws_lambda_function.app_v1_lambda_main[each.key].function_name}"

  retention_in_days = var.retention
}