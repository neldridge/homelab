resource "aws_route53_record" "route53_record" {
  zone_id = var.zone_id
  name    = var.name
  type    = var.type
  ttl     = var.ttl
  records = var.records
}
output "name" {
  value = aws_route53_record.route53_record.name
}
output "fqdn" {
  value = aws_route53_record.route53_record.fqdn
}
output "type" {
  value = aws_route53_record.route53_record.type
}
output "ttl" {
  value = aws_route53_record.route53_record.ttl
}
output "records" {
  value = aws_route53_record.route53_record.records
}
output "zone_id" {
  value = aws_route53_record.route53_record.zone_id
}

variable "zone_id" {
  type = string
}

variable "name" {
  type = string
}

variable "type" {
  type = string
}

variable "ttl" {
  type    = number
  default = 60
}

variable "records" {
  type = list(string)
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
