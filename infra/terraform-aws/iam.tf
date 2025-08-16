######################################
# EC2 Instance Role + Instance Profile
######################################

# Trust policy so EC2 can assume this role
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "chat_ec2_role" {
  name               = "chat-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

# Least-privilege inline policy to read only our parameters
# and decrypt SecureString (KMS is required for SecureString)
data "aws_iam_policy_document" "ssm_read_params" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      aws_ssm_parameter.db_root_pass.arn,
      aws_ssm_parameter.db_pass.arn,
      aws_ssm_parameter.openai_api_key.arn
    ]
  }

  # Needed to read SecureString parameters
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    # SecureString in SSM uses AWS managed key alias/aws/ssm
    # We allow decrypt on that key; the exact key ARN varies per account/region,
    # so simplest is "*" with a safety condition that it must be via SSM in our region.
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region}.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "ssm_read_params" {
  name        = "chat-ssm-read-params"
  description = "Allow EC2 to read specific SSM parameters for chat app"
  policy      = data.aws_iam_policy_document.ssm_read_params.json
}

# (Optional but handy) Attach the AWS-managed policy so the instance can be managed by SSM
# Not required for Parameter Store reads, but useful later for SSM Session Manager, etc.
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.chat_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach our custom policy
resource "aws_iam_role_policy_attachment" "attach_ssm_read_params" {
  role       = aws_iam_role.chat_ec2_role.name
  policy_arn = aws_iam_policy.ssm_read_params.arn
}

resource "aws_iam_instance_profile" "chat_profile" {
  name = "chat-ec2-instance-profile"
  role = aws_iam_role.chat_ec2_role.name
}
