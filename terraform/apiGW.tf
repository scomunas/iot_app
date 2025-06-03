######################################
## API Gateway Creation + API Key + Usage Plan
######################################

##############################
# REST API
##############################
resource "aws_api_gateway_rest_api" "app_v1_rest_api" {
  name = "app-v1-rest-api"
}

##############################
# LOCAL VARIABLES
##############################
locals {
  versions = distinct([for l in values(var.lambdas) : l.version])

  lambda_paths = {
    for key, val in var.lambdas :
    key => [val.version, val.apiPath]
  }
}

##############################
# API RESOURCES
##############################
resource "aws_api_gateway_resource" "app_v1_rest_version" {
  for_each = toset(var.versions)

  rest_api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
  parent_id   = aws_api_gateway_rest_api.app_v1_rest_api.root_resource_id
  path_part   = each.key
}

resource "aws_api_gateway_resource" "app_v1_rest_path" {
  for_each = {
    for combo in flatten([
      for v in var.versions : [
        for p in var.paths : {
          key     = "${v}/${p}"
          version = v
          path    = p
        }
      ]
    ]) : combo.key => combo
  }

  rest_api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
  parent_id   = aws_api_gateway_resource.app_v1_rest_version[each.value.version].id
  path_part   = each.value.path
}

##############################
# API METHODS
##############################
resource "aws_api_gateway_method" "app_v1_lambda_method" {
  for_each = var.lambdas

  rest_api_id      = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id      = aws_api_gateway_resource.app_v1_rest_path["${each.value.version}/${each.value.apiPath}"].id
  http_method      = each.value.apiMethod
  authorization    = "NONE"
  api_key_required = true
}

##############################
# LAMBDA INTEGRATION
##############################
resource "aws_api_gateway_integration" "app_v1_lambda_integration" {
  for_each = var.lambdas

  rest_api_id             = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id             = aws_api_gateway_resource.app_v1_rest_path["${each.value.version}/${each.value.apiPath}"].id
  http_method             = aws_api_gateway_method.app_v1_lambda_method[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.app_v1_lambda_main[each.key].invoke_arn
}

##############################
# CORS OPTIONS METHOD AND INTEGRATION (one OPTIONS per resource)
##############################
resource "aws_api_gateway_method" "app_v1_cors_options" {
  for_each = aws_api_gateway_resource.app_v1_rest_path

  rest_api_id      = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id      = each.value.id
  http_method      = "OPTIONS"
  authorization    = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "app_v1_cors_options_integration" {
  for_each = aws_api_gateway_resource.app_v1_rest_path

  rest_api_id             = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id             = each.value.id
  http_method             = aws_api_gateway_method.app_v1_cors_options[each.key].http_method
  integration_http_method = "OPTIONS"
  type                    = "MOCK"

  request_templates = {
    "application/json" = <<EOF
{
  "statusCode": 200
}
EOF
  }
}

resource "aws_api_gateway_method_response" "app_v1_cors_method_response" {
  for_each = aws_api_gateway_resource.app_v1_rest_path

  rest_api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id = each.value.id
  http_method = aws_api_gateway_method.app_v1_cors_options[each.key].http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "app_v1_cors_integration_response" {
  for_each = aws_api_gateway_resource.app_v1_rest_path

  rest_api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
  resource_id = each.value.id
  http_method = aws_api_gateway_method.app_v1_cors_options[each.key].http_method
  status_code = aws_api_gateway_method_response.app_v1_cors_method_response[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,PUT,POST,DELETE'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

##############################
# API KEY and USAGE PLAN
##############################
resource "aws_api_gateway_api_key" "app_key" {
  name    = "app_api_key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "app_usage_plan" {
  name = "app_usage_plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
    stage  = aws_api_gateway_deployment.app_v1_app_deployment.stage_name
  }

  throttle_settings {
    burst_limit = 100
    rate_limit  = 50
  }
}

resource "aws_api_gateway_usage_plan_key" "app_usage_plan_key" {
  key_id        = aws_api_gateway_api_key.app_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.app_usage_plan.id
}

##############################
# DEPLOYMENT AND STAGE
##############################
resource "aws_api_gateway_deployment" "app_v1_app_deployment" {
  depends_on = [
    aws_api_gateway_integration.app_v1_lambda_integration,
    aws_api_gateway_integration.app_v1_cors_options_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.app_v1_rest_api.id
  stage_name  = "prod"
}
