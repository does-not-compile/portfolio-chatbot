#!/bin/bash
set -e

# Update & install dependencies
apt-get update -y
apt-get install -y docker.io docker-compose jq unzip curl

# Ensure AWS CLI v2 is installed
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip /tmp/awscliv2.zip -d /tmp
    /tmp/aws/install
fi

# Start Docker
systemctl enable docker
systemctl start docker

# Fetch secrets from AWS SSM Parameter Store
DB_ROOT_PASS=$$(aws ssm get-parameter --name "/chatapp/db_root_pass" --with-decryption --query "Parameter.Value" --output text --region $${region})
DB_PASS=$$(aws ssm get-parameter --name "/chatapp/db_pass" --with-decryption --query "Parameter.Value" --output text --region $${region})
DB_USER=$$(aws ssm get-parameter --name "/chatapp/db_user" --query "Parameter.Value" --output text --region $${region})
DB_NAME=$$(aws ssm get-parameter --name "/chatapp/db_name" --query "Parameter.Value" --output text --region $${region})
OPENAI_API_KEY=$$(aws ssm get-parameter --name "/chatapp/openai_api_key" --with-decryption --query "Parameter.Value" --output text --region $${region})

# Export environment variables for Docker Compose
export DB_ROOT_PASS DB_PASS DB_USER DB_NAME OPENAI_API_KEY

# Save env vars to a profile so they persist for login sessions if needed
echo "export DB_ROOT_PASS=$${DB_ROOT_PASS}" >> /etc/profile.d/chatapp_env.sh
echo "export DB_PASS=$${DB_PASS}" >> /etc/profile.d/chatapp_env.sh
echo "export DB_USER=$${DB_USER}" >> /etc/profile.d/chatapp_env.sh
echo "export DB_NAME=$${DB_NAME}" >> /etc/profile.d/chatapp_env.sh
echo "export OPENAI_API_KEY=$${OPENAI_API_KEY}" >> /etc/profile.d/chatapp_env.sh
chmod +x /etc/profile.d/chatapp_env.sh

# Navigate to app folder (assumes mounted or cloned by Terraform)
cd /app

# Start Docker Compose
docker-compose up -d
