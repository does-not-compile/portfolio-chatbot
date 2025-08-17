#cloud-boothook
#!/bin/bash
exec > >(tee /var/log/user_data.log | logger -t user_data -s 2>/dev/console) 2>&1
set -euxo pipefail

# Ensure noninteractive
export DEBIAN_FRONTEND=noninteractive

# Update & install base packages
apt-get update -y
apt-get install -y -q \
    docker.io docker-compose jq unzip curl git

# Start Docker
systemctl enable docker
systemctl start docker

# Add default user (Ubuntu) to docker group so it's usable later
usermod -aG docker ubuntu || true

# Install AWS CLI v2 if not present
if ! command -v aws &>/dev/null; then
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp
    /tmp/aws/install
fi

# Fetch secrets from AWS SSM
REGION="${region}"   # passed from Terraform template var
DB_ROOT_PASS=$(aws ssm get-parameter --name "/chatapp/db_root_pass" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_PASS=$(aws ssm get-parameter --name "/chatapp/db_pass" --with-decryption --query "Parameter.Value" --output text --region "$REGION")
DB_USER=$(aws ssm get-parameter --name "/chatapp/db_user" --query "Parameter.Value" --output text --region "$REGION")
DB_NAME=$(aws ssm get-parameter --name "/chatapp/db_name" --query "Parameter.Value" --output text --region "$REGION")
OPENAI_API_KEY=$(aws ssm get-parameter --name "/chatapp/openai_api_key" --with-decryption --query "Parameter.Value" --output text --region "$REGION")

# Export for docker-compose only (not globally persisted!)
export DB_ROOT_PASS DB_PASS DB_USER DB_NAME OPENAI_API_KEY

# Clone app and start Docker in background
(
    set -e
    rm -rf /app
    git clone https://github.com/does-not-compile/portfolio-chatbot.git /app
    cd /app
    # Run detached with env vars injected
    docker-compose up -d
) &

echo "User data script finished at $(date)"
