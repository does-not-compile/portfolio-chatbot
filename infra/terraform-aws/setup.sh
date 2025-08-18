#!/usr/bin/env bash
set -euo pipefail

REGION="eu-central-1"
APP_DIR="$HOME/app"
ENV_FILE="$APP_DIR/app/.env"
DOMAIN="chat.snagel.io"
EMAIL="sebastian.nagel1@gmx.com"

# --- Install system packages ---
sudo apt-get update -y
sudo apt-get install -y -q docker.io docker-compose jq unzip curl git nginx certbot python3-certbot-nginx

# --- Enable services ---
sudo systemctl enable docker && sudo systemctl start docker
sudo systemctl enable nginx && sudo systemctl start nginx
sudo usermod -aG docker ubuntu

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

# --- Export variables for Docker and shell ---
export DB_ROOT_PASS DB_PASS DB_USER DB_NAME OPENAI_API_KEY

# --- Deploy app ---
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

cd "$APP_DIR/app"
sudo docker-compose up --build -d

# --- Configure Nginx ---
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
WEBROOT="/var/www/certbot"

# Create webroot dir for ACME challenges
sudo mkdir -p "$WEBROOT"
sudo chown -R www-data:www-data "$WEBROOT"

# Initial HTTP server for ACME challenge
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Serve ACME challenge files
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }

    # Proxy all other traffic to app
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# --- Issue cert via webroot ---
sudo certbot certonly --webroot -w "$WEBROOT" -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

# --- Update Nginx to use SSL with redirect and HSTS ---
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # HSTS header
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx

# --- Add cron job for cert renewal ---
(crontab -l 2>/dev/null; echo "0 0,12 * * * certbot renew --quiet && systemctl reload nginx") | crontab -
