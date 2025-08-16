# Find latest Ubuntu 24.04 LTS in eu-central-1
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
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
  description = "Allow HTTP, HTTPS, SSH, and DB"

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
  iam_instance_profile        = aws_iam_instance_profile.chat_profile.name
  user_data = templatefile("${path.module}/user_data.sh.tpl", {
    region = var.aws_region
  })


  tags = {
    Name = "chat-app-server"
  }
}

# Elastic IP (static)
resource "aws_eip" "chat_app_eip" {
  instance = aws_instance.chat_app.id
}

# SSM Parameters (encrypted with KMS by default)
resource "aws_ssm_parameter" "db_root_pass" {
  name        = "/chatapp/db_root_pass"
  type        = "SecureString"
  value       = var.db_root_pass
}

resource "aws_ssm_parameter" "db_pass" {
  name        = "/chatapp/db_pass"
  type        = "SecureString"
  value       = var.db_pass
}

resource "aws_ssm_parameter" "openai_api_key" {
  name        = "/chatapp/openai_api_key"
  type        = "SecureString"
  value       = var.openai_api_key
}
