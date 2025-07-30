import vertexai
from vertexai import agent_engines

vertexai.init(
    project="svc-hackathon-prod07",
    location="us-central1",
    staging_bucket="gs://mcp-events",
)
