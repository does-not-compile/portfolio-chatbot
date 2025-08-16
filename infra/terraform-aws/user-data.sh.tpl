#!/bin/bash
set -e

# Update & install dependencies
apt-get update -y
apt-get install -y docker.io docker-compose jq awscli

# Start Docker
systemctl enable docker
systemctl start docker

# Fetch secrets from AWS SSM Parameter Store
DB_ROOT_PASS=$(aws ssm get-parameter --name "/chatapp/db_root_pass" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})
DB_PASS=$(aws ssm get-parameter --name "/chatapp/db_pass" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})
DB_USER=$(aws ssm get-parameter --name "/chatapp/db_user" --query "Parameter.Value" --output text --region ${aws_region})
DB_NAME=$(aws ssm get-parameter --name "/chatapp/db_name" --query "Parameter.Value" --output text --region ${aws_region})
OPENAI_API_KEY=$(aws ssm get-parameter --name "/chatapp/openai_api_key" --with-decryption --query "Parameter.Value" --output text --region ${aws_region})

# Export environment variables for Docker Compose
export DB_ROOT_PASS DB_PASS DB_USER DB_NAME OPENAI_API_KEY

# Navigate to app folder (assumes mounted or cloned by Terraform)
cd /app

# Start Docker Compose
docker-compose up -d
