resource "aws_s3_bucket" "app_v1_bucket" {
  bucket        = "app-iot-v1-bucket"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "app_v1_bucket_access" {
  bucket = aws_s3_bucket.app_v1_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
