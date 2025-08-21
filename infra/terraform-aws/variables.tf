variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small" # 2 GB RAM, as you wanted
}

variable "key_name" {
  description = "Name of your AWS key pair for SSH"
  type        = string
}

variable "public_key_path" {
  description = "Path to your local SSH public key"
  type        = string
}

variable "private_key_path" {
  description = "Path to your private SSH key for EC2"
  type        = string
}

variable "ami_id" {
  description = "Optional: manually set an AMI ID. Leave empty to auto-select Ubuntu 24.04"
  type        = string
  default     = ""
}