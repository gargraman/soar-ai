
# AWS Bedrock Setup for Claude 3.5 Sonnet

This guide explains how to configure AWS Bedrock to use Claude 3.5 Sonnet for AI-powered cybersecurity event analysis.

## 🔑 AWS Credentials Setup

### Option 1: AWS CLI Configuration (Recommended)
```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure AWS credentials
aws configure
```

Enter your credentials when prompted:
- AWS Access Key ID: `Your access key`
- AWS Secret Access Key: `Your secret key`
- Default region name: `us-east-1`
- Default output format: `json`

### Option 2: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_DEFAULT_REGION=us-east-1
```

### Option 3: IAM Role (For EC2/Lambda)
If running on AWS infrastructure, configure an IAM role with Bedrock permissions.

## 🔐 Required IAM Permissions

Create an IAM policy with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": [
                "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
            ]
        }
    ]
}
```

## 🌐 Model Access Request

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Go to "Model access" in the left sidebar
4. Request access to "Claude 3.5 Sonnet v2" by Anthropic
5. Wait for approval (usually instant for Claude models)

## 🔧 Configuration

The application is pre-configured to use:
- **Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Region**: `us-east-1`
- **Max Tokens**: 2000
- **Temperature**: 0.1 (for consistent security analysis)

You can modify these settings in `src/config/settings.py`:

```python
self.ai_config = {
    "provider": "aws_bedrock",
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0", 
    "region": "us-east-1",
    "max_tokens": 2000,
    "temperature": 0.1,
    "fallback_to_rules": True
}
```

## 🧪 Testing the Setup

1. Start the application: `python main.py`
2. Upload a sample security event
3. Use prompt: "Analyze this event for security threats"
4. Check the results for Claude's AI analysis

## 💰 Cost Considerations

Claude 3.5 Sonnet pricing (as of 2024):
- Input: $3.00 per million tokens
- Output: $15.00 per million tokens

Typical security event analysis uses ~500-1000 tokens per event, making it very cost-effective for cybersecurity automation.

## 🔄 Fallback Behavior

If Claude is unavailable or fails:
- The system automatically falls back to rule-based analysis
- Logs the failure for debugging
- Continues processing events without interruption
- Set `fallback_to_rules: false` to disable this behavior

## 🛠️ Troubleshooting

### Common Issues:

**"Model access denied"**
- Ensure you've requested access to Claude 3.5 Sonnet in Bedrock console
- Verify your AWS region is us-east-1

**"Credentials not found"**
- Run `aws configure` to set up credentials
- Check environment variables are set correctly

**"Region not supported"**
- Claude 3.5 Sonnet is only available in us-east-1
- Update your region configuration if needed

**High latency/timeouts**
- Consider using Claude 3 Haiku for faster responses
- Reduce max_tokens for shorter responses
- Implement request retry logic

## 🔍 Monitoring Usage

Monitor your Bedrock usage in AWS Console:
1. Go to CloudWatch
2. Select "Bedrock" metrics
3. Monitor token usage and costs
4. Set up billing alerts if needed
