resource "aws_dynamodb_table" "app_v1_temperature" {
  name             = "app-v1-temperature"
  billing_mode     = "PAY_PER_REQUEST"
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "sensor"
    type = "S"
  }

  attribute {
    name = "event_date"
    type = "S"
  }

  ttl {
    enabled        = true
    attribute_name = "event_date_ttl"
  }

  hash_key  = "sensor"
  range_key = "event_date"

  # attribute {
  #     name = "state"
  #     type = "S"
  # }

  # global_secondary_index {
  #     name               = "state_index"
  #     hash_key           = "state"
  #     range_key          = "event_date"
  #     projection_type    = "ALL"
  # }
}
