# Google Vertex AI Gemini Provider Documentation

## Overview

The `GoogleVertexGeminiProvider` is a new AI provider that integrates with Google's Vertex AI platform using the native `vertexai.generative_models` module. This provider offers advanced capabilities using Google's Gemini 1.5 Pro model for cybersecurity event analysis.

## Features

- **Native Vertex AI Integration**: Direct integration with Google's Vertex AI platform
- **Gemini 1.5 Pro Support**: Utilizes Google's latest Gemini model
- **Advanced Generation Parameters**: Supports fine-tuning with top_p, top_k parameters
- **Automatic JSON Parsing**: Handles both JSON and plain text responses
- **Lazy Initialization**: Efficient resource usage with on-demand client creation
- **Error Handling**: Robust error handling and fallback mechanisms

## Configuration

### Basic Configuration

```json
{
  "ai_config": {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
      "model": "gemini-1.5-pro",
      "project_id": "your-gcp-project-id",
      "location": "us-central1"
    }
  }
}
```

### Advanced Configuration

```json
{
  "ai_config": {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
      "model": "gemini-1.5-pro",
      "project_id": "your-gcp-project-id",
      "location": "us-central1",
      "max_tokens": 2000,
      "temperature": 0.1,
      "top_p": 0.8,
      "top_k": 40
    }
  }
}
```

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `gemini-1.5-pro` | The Gemini model to use |
| `project_id` | string | **Required** | Your Google Cloud Project ID |
| `location` | string | `us-central1` | The Google Cloud region |
| `max_tokens` | integer | `2000` | Maximum tokens in response |
| `temperature` | float | `0.1` | Controls randomness (0.0-1.0) |
| `top_p` | float | `0.8` | Nucleus sampling parameter |
| `top_k` | integer | `40` | Top-k sampling parameter |

## Setup Instructions

### 1. Install Dependencies

```bash
pip install vertexai google-generativeai google-cloud-aiplatform
```

### 2. Configure Google Cloud Authentication

Set up Application Default Credentials:

```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 3. Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### 4. Update Configuration

Update your `src/config/settings.py` or configuration JSON file to use the new provider:

```python
self.ai_config = {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
        "model": "gemini-1.5-pro",
        "project_id": "your-actual-project-id",
        "location": "us-central1",
        "max_tokens": 2000,
        "temperature": 0.1,
        "top_p": 0.8,
        "top_k": 40
    },
    "fallback_to_rules": True
}
```

## Usage Examples

### Basic Usage

```python
from ai_provider import GoogleVertexGeminiProvider

# Configure the provider
config = {
    "model": "gemini-1.5-pro",
    "project_id": "my-project",
    "location": "us-central1"
}

provider = GoogleVertexGeminiProvider(config)

# Analyze a security event
event_data = {
    "src_ip": "192.168.1.100",
    "event_type": "suspicious_connection"
}
user_prompt = "Check if this IP is malicious"

result = await provider.analyze_security_event(event_data, user_prompt)
print(result)
```

### Using the Factory Pattern

```python
from ai_provider import AIProviderFactory

ai_config = {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
        "model": "gemini-1.5-pro",
        "project_id": "my-project",
        "location": "us-central1"
    }
}

provider = AIProviderFactory.create_provider(ai_config)
result = await provider.analyze_security_event(event_data, user_prompt)
```

## Response Format

The provider returns a standardized response format:

```json
{
  "actions": [
    {
      "server": "virustotal",
      "action": "ip_report",
      "parameters": {"ip": "192.168.1.100"}
    }
  ],
  "reasoning": "Suspicious IP detected, checking reputation with VirusTotal",
  "severity": "medium",
  "priority": 3
}
```

## Model Comparison

| Provider | Model | Strengths | Use Cases |
|----------|-------|-----------|-----------|
| AWS Bedrock | Claude 3.5 Sonnet | Advanced reasoning, code analysis | Complex threat analysis |
| Google Vertex (Claude) | Claude 3.5 Sonnet | Anthropic's reasoning via GCP | GCP-native Claude deployment |
| **Google Vertex (Gemini)** | **Gemini 1.5 Pro** | **Native Google integration, multimodal** | **Fast analysis, cost-effective** |

## Performance Characteristics

- **Latency**: ~1-3 seconds for typical security event analysis
- **Token Efficiency**: Optimized for cybersecurity prompts
- **Cost**: Generally more cost-effective than Claude models
- **Availability**: High availability through Google Cloud infrastructure

## Error Handling

The provider includes comprehensive error handling:

```python
try:
    result = await provider.analyze_security_event(event_data, user_prompt)
except Exception as e:
    logger.error(f"Gemini analysis failed: {e}")
    # Automatic fallback to rule-based analysis
    result = RuleBasedFallback.analyze_security_event(event_data, user_prompt)
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all AI provider tests
pytest tests/test_client/test_ai_provider.py -v

# Run specific Gemini tests
pytest tests/test_client/test_ai_provider.py::TestGoogleVertexGeminiProvider -v
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   google.auth.exceptions.DefaultCredentialsError
   ```
   **Solution**: Run `gcloud auth application-default login`

2. **Project Not Found**
   ```
   Project 'your-project' not found
   ```
   **Solution**: Verify your project ID and ensure APIs are enabled

3. **Permission Denied**
   ```
   Permission 'aiplatform.endpoints.predict' denied
   ```
   **Solution**: Ensure your account has Vertex AI User role

4. **Model Not Available**
   ```
   Model 'gemini-1.5-pro' not found in location 'us-central1'
   ```
   **Solution**: Check model availability in your region

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your analysis
result = await provider.analyze_security_event(event_data, user_prompt)
```

## Migration from Other Providers

### From AWS Bedrock

```python
# Before (AWS Bedrock)
ai_config = {
    "provider": "aws_bedrock",
    "aws_bedrock": {
        "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "region": "us-east-1"
    }
}

# After (Google Vertex Gemini)
ai_config = {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
        "model": "gemini-1.5-pro",
        "project_id": "your-project-id",
        "location": "us-central1"
    }
}
```

### From Google Vertex Claude

```python
# Before (Vertex Claude)
ai_config = {
    "provider": "google_vertex",
    "google_vertex": {
        "model": "claude-3-5-sonnet@20241022",
        "project_id": "your-project-id"
    }
}

# After (Vertex Gemini)
ai_config = {
    "provider": "google_vertex_gemini",
    "google_vertex_gemini": {
        "model": "gemini-1.5-pro",
        "project_id": "your-project-id"
    }
}
```

## Best Practices

1. **Use Environment Variables** for sensitive configuration:
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

2. **Implement Retry Logic** for production use:
   ```python
   import asyncio
   
   async def analyze_with_retry(provider, event_data, user_prompt, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await provider.analyze_security_event(event_data, user_prompt)
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

3. **Monitor Usage and Costs** through Google Cloud Console

4. **Use Appropriate Regions** for data residency requirements

## Integration with MCP Servers

The Gemini provider works seamlessly with all MCP servers:

- **VirusTotal**: IP/domain/file reputation checks
- **ServiceNow**: Incident creation and management
- **CyberReason**: Endpoint investigation
- **Custom REST**: Generic API integrations

Example analysis that uses multiple servers:

```json
{
  "actions": [
    {
      "server": "virustotal",
      "action": "ip_report",
      "parameters": {"ip": "192.168.1.100"}
    },
    {
      "server": "servicenow",
      "action": "create_record",
      "parameters": {
        "type": "incident",
        "summary": "Suspicious IP detected",
        "priority": 3
      }
    },
    {
      "server": "cyberreason",
      "action": "get_pylum_id",
      "parameters": {"hostname": "workstation-01"}
    }
  ],
  "reasoning": "Multi-step analysis: check IP reputation, create tracking ticket, investigate endpoint",
  "severity": "medium",
  "priority": 3
}
```

## Support and Resources

- **Google Vertex AI Documentation**: https://cloud.google.com/vertex-ai/docs
- **Gemini Model Documentation**: https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini
- **Python Client Library**: https://googleapis.dev/python/aiplatform/latest/
- **Pricing**: https://cloud.google.com/vertex-ai/pricing
