$resources = @(
    "fixTemperature",
    "getBlindStatus",
    "getLightStatus",
    "getSunrise",
    "getTemperature",
    "setBlindPosition",
    "setTemperature"
)

$targets = @()

foreach ($res in $resources) {
    $method_target = "aws_api_gateway_method.app_v1_lambda_method[`"$res`"]"
    $integration_target = "aws_api_gateway_integration.app_v1_lambda_integration[`"$res`"]"

    # Escapamos las comillas internas duplicándolas para PowerShell
    $method_target_escaped = $method_target -replace '"', '""'
    $integration_target_escaped = $integration_target -replace '"', '""'

    $targets += "-target=""$method_target_escaped"""
    $targets += "-target=""$integration_target_escaped"""
}

$targets += "-target=aws_api_gateway_deployment.app_v1_app_deployment"

# Mostrar el comando completo
$cmd = "terraform destroy " + ($targets -join ' ')
Write-Output $cmd
