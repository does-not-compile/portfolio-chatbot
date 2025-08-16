output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.chat_app.public_ip
}

output "instance_eip" {
  description = "Elastic IP of the EC2 instance"
  value       = aws_eip.chat_app_eip.public_ip
}
