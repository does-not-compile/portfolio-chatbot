resource "aws_secretsmanager_secret" "chat_db" {
  name        = "chat-db-credentials"
  description = "Database credentials for Chatbot app"
}

resource "aws_secretsmanager_secret_version" "chat_db_values" {
  secret_id     = aws_secretsmanager_secret.chat_db.id
  secret_string = jsonencode({
    DB_USER       = var.db_user
    DB_PASS       = var.db_pass
    DB_ROOT_PASS  = var.db_root_pass
    DB_NAME       = var.db_name
    OPENAI_API_KEY = var.openai_api_key
  })
}
