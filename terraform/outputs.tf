############################################
## Show URL for API GW
############################################
output "iot_api_gw_url" {
  value = aws_api_gateway_deployment.app_v1_app_deployment.invoke_url
}

# output "iot_sqs_queue_url" {
#   value = aws_sqs_queue.app_v1_sqs_queue.url
# }

output "api_gateway_api_key" {
  value       = aws_api_gateway_api_key.app_key.value
  description = "API Key value (sensitive)"
  sensitive   = true  # pon true si no quieres que se muestre en consola
}