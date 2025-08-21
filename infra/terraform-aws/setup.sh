#!/usr/bin/env bash
set -euo pipefail

REGION="eu-central-1"
APP_DIR="$HOME/app"
ENV_FILE="$APP_DIR/.env"
DOMAIN="chat.snagel.io"
EMAIL="sebastian.nagel1@gmx.com"

# --- Install system packages ---
sudo apt-get update -y
sudo apt-get install -y -q docker.io docker-compose git unzip curl jq

# --- Enable Docker ---
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker "$USER"

# --- Install AWS CLI if missing ---
if ! command -v aws &>/dev/null; then
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
    unzip -q /tmp/awscliv2.zip -d /tmp
    sudo /tmp/aws/install
fi

# --- Fetch SSM parameters with retry ---
for i in {1..12}; do
    echo "Fetching SSM parameters (attempt $i)..."
    DB_ROOT_PASS=$(aws ssm get-parameter --name '/chatapp/db_root_pass' --with-decryption --query 'Parameter.Value' --output text --region "$REGION") \
      && DB_PASS=$(aws ssm get-parameter --name '/chatapp/db_pass' --with-decryption --query 'Parameter.Value' --output text --region "$REGION") \
      && DB_USER=$(aws ssm get-parameter --name '/chatapp/db_user' --query 'Parameter.Value' --output text --region "$REGION") \
      && DB_NAME=$(aws ssm get-parameter --name '/chatapp/db_name' --query 'Parameter.Value' --output text --region "$REGION") \
      && OPENAI_API_KEY=$(aws ssm get-parameter --name '/chatapp/openai_api_key' --with-decryption --query 'Parameter.Value' --output text --region "$REGION") \
      && break
    sleep 5
done

# --- Export variables for Docker ---
export DB_ROOT_PASS DB_PASS DB_USER DB_NAME OPENAI_API_KEY
export VIRTUAL_HOST=$DOMAIN
export LETSENCRYPT_HOST=$DOMAIN
export LETSENCRYPT_EMAIL=$EMAIL

# --- Clone app repo ---
rm -rf "$APP_DIR"
git clone https://github.com/does-not-compile/portfolio-chatbot.git "$APP_DIR"

# --- Write .env file ---
cat > "$ENV_FILE" <<EOF
DB_ROOT_PASS=$DB_ROOT_PASS
DB_PASS=$DB_PASS
DB_USER=$DB_USER
DB_NAME=$DB_NAME
OPENAI_API_KEY=$OPENAI_API_KEY
EOF

# --- Stop SSM to free ports ---
sudo systemctl stop amazon-ssm-agent || true

# --- Start all Docker services ---
cd "$APP_DIR"
sudo docker-compose up -d --build

# --- Wait for nginx-proxy and letsencrypt to initialize ---
sleep 10
sudo docker logs nginx-proxy || true
sudo docker logs letsencrypt || true

# --- Restart SSM agent ---
sudo systemctl start amazon-ssm-agent || true

echo "Setup complete. Your app should be reachable at https://$DOMAIN"
