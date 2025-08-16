variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro" # free-tier eligible, cheapest
}

variable "key_name" {
  description = "Name of your AWS key pair for SSH"
  type        = string
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "chatuser"
}

variable "db_pass" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "chatdb"
}
