######################################
# EC2 Instance Role + Instance Profile
######################################

# Get account info for IAM ARNs
data "aws_caller_identity" "current" {}

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

# Least-privilege inline policy to read our parameters
data "aws_iam_policy_document" "ssm_read_params" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    # Use wildcard to avoid referencing deleted aws_ssm_parameter resources
    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/chatapp/*"
    ]
  }

  # Needed to read SecureString parameters
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    # Allow decrypt on any key via SSM in our region
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

# Attach the AWS-managed policy for SSM Session Manager (optional)
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.chat_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach our custom SSM read policy
resource "aws_iam_role_policy_attachment" "attach_ssm_read_params" {
  role       = aws_iam_role.chat_ec2_role.name
  policy_arn = aws_iam_policy.ssm_read_params.arn
}

resource "aws_iam_instance_profile" "chat_profile" {
  name = "chat-ec2-instance-profile"
  role = aws_iam_role.chat_ec2_role.name
}
