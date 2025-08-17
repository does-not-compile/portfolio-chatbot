# Find the latest Ubuntu 24.x LTS AMI (x86_64) in the current region
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}


# Key pair (for SSH access)
resource "aws_key_pair" "deployer" {
  key_name   = var.key_name
  public_key = file(var.public_key_path)
}

# Security group for EC2
resource "aws_security_group" "chat_sg" {
  name        = "chat-app-sg"
  description = "Allow HTTP, HTTPS, SSH, and App"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "App"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "all"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instance
resource "aws_instance" "chat_app" {
  ami           = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.chat_sg.id]
  iam_instance_profile  = aws_iam_instance_profile.chat_profile.name

  tags = {
    Name = "chat-app-server"
  }

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.private_key_path)
      host        = self.public_ip
    }

    inline = [
            # Install packages
      "bash -c 'sudo apt-get update -y && sudo apt-get install -y -q docker.io docker-compose jq unzip curl git nginx certbot python3-certbot-nginx'",

      # Enable services
      "sudo systemctl enable docker && sudo systemctl start docker",
      "sudo systemctl enable nginx && sudo systemctl start nginx",
      "sudo usermod -aG docker ubuntu",

      # Configure Nginx reverse proxy for chat.snagel.io
      "echo 'server { listen 80; server_name chat.snagel.io; location / { proxy_pass http://127.0.0.1:8000; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection \"upgrade\"; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; } }' | sudo tee /etc/nginx/sites-available/chat.snagel.io",
      "sudo ln -s /etc/nginx/sites-available/chat.snagel.io /etc/nginx/sites-enabled/",
      "sudo rm -f /etc/nginx/sites-enabled/default",
      "sudo nginx -t && sudo systemctl reload nginx",

      # Get parameters from AWS SSM (same as before)
      "if ! command -v aws &>/dev/null; then curl -s 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o '/tmp/awscliv2.zip' && unzip -q /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install; fi",
      "export REGION='eu-central-1'",
      "export DB_ROOT_PASS=$(aws ssm get-parameter --name '/chatapp/db_root_pass' --with-decryption --query 'Parameter.Value' --output text --region $REGION)",
      "export DB_PASS=$(aws ssm get-parameter --name '/chatapp/db_pass' --with-decryption --query 'Parameter.Value' --output text --region $REGION)",
      "export DB_USER=$(aws ssm get-parameter --name '/chatapp/db_user' --query 'Parameter.Value' --output text --region $REGION)",
      "export DB_NAME=$(aws ssm get-parameter --name '/chatapp/db_name' --query 'Parameter.Value' --output text --region $REGION)",
      "export OPENAI_API_KEY=$(aws ssm get-parameter --name '/chatapp/openai_api_key' --with-decryption --query 'Parameter.Value' --output text --region $REGION)",

      # Deploy chatbot
      "rm -rf ~/app",
      "git clone https://github.com/does-not-compile/portfolio-chatbot.git ~/app",
      "cd ~/app/app",
      "sudo docker-compose up -d",

      # Enable HTTPS with Let's Encrypt
      "sudo certbot --nginx -d chat.snagel.io --non-interactive --agree-tos -m sebastian.nagel1@gmx.com || true",

      # Add cron job for cert renewal (twice daily)
      "(crontab -l 2>/dev/null; echo \"0 0,12 * * * certbot renew --quiet && systemctl reload nginx\") | crontab -"
    ]
  }
}

# Elastic IP (static)
resource "aws_eip" "chat_app_eip" {
  instance = aws_instance.chat_app.id
}
