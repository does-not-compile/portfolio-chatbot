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

  # Ensure instance gets a public IP
  associate_public_ip_address = true

  tags = {
    Name = "chat-app-server"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_path)
    host        = self.public_ip
  }
  
  provisioner "file" {
    source      = "setup.sh"
    destination = "/home/ubuntu/setup.sh"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x ~/setup.sh",
      "bash ~/setup.sh"
    ]
  }
}

# Elastic IP (static)
resource "aws_eip" "chat_app_eip" {
  instance = aws_instance.chat_app.id
  # Ensure the EIP is in the same VPC (for default VPC, optional)
  domain = "vpc"
}
