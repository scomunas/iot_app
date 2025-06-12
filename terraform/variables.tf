variable "versions" {
  type    = list(string)
  default = ["v1"]
}

variable "paths" {
  type    = list(string)
  default = ["temperature", "blinds", "sunrise", "lights"]
}

variable "lambdas" {
  type = map(object({
    name      = string
    handler   = string
    version   = string
    apiPath   = string
    apiMethod = string
  }))
  default = {
    "setTemperature" = {
      "name" : "app-v1-set-temperature",
      "handler" : "temperature.set_temperature",
      "version" : "v1",
      "apiPath" : "temperature",
      "apiMethod" : "POST"
    },
    "fixTemperature" = {
      "name" : "app-v1-fix-temperature",
      "handler" : "temperature.fix_temperature",
      "version" : "v1",
      "apiPath" : "temperature",
      "apiMethod" : "PUT"
    },
    "getTemperature" = {
      "name" : "app-v1-get-temperature",
      "handler" : "temperature.get_temperature",
      "version" : "v1",
      "apiPath" : "temperature",
      "apiMethod" : "GET"
    },
    "getBlindStatus" = {
      "name" : "app-v1-get-blind-status",
      "handler" : "blinds.get_blind_state",
      "version" : "v1",
      "apiPath" : "blinds",
      "apiMethod" : "GET"
    },
    "setBlindPosition" = {
      "name" : "app-v1-set-blind-position",
      "handler" : "blinds.set_blind_position",
      "version" : "v1",
      "apiPath" : "blinds",
      "apiMethod" : "POST"
    },
    "getSunrise" = {
      "name" : "app-v1-get-sunrise",
      "handler" : "sunrise.get_sunrise",
      "version" : "v1",
      "apiPath" : "sunrise",
      "apiMethod" : "GET"
    },
    "getLightStatus" = {
      "name" : "app-v1-get-light-status",
      "handler" : "lights.get_light_state",
      "version" : "v1",
      "apiPath" : "lights",
      "apiMethod" : "GET"
    },
    "setLightAction" = {
      "name" : "app-v1-set-light-action",
      "handler" : "lights.set_light_action",
      "version" : "v1",
      "apiPath" : "lights",
      "apiMethod" : "POST"
    }
  }
}

variable "retention" {
  # Retention in days
  # valid for log and DynamoDB
  type    = number
  default = 7
}

variable "lambda_timeout" {
  # Lambda timeout in seconds
  type    = number
  default = 25
}
