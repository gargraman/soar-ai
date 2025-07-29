#!/usr/bin/env python3
"""
Demonstration script for the new Google Vertex AI Gemini provider.

This script shows how to:
1. Configure the Gemini provider
2. Analyze security events
3. Handle different response scenarios
4. Compare with other providers
"""

import asyncio
import json
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'client')))

from ai_provider import (
    AWSBedrockProvider,
    GoogleVertexProvider, 
    GoogleVertexGeminiProvider,
    AIProviderFactory,
    RuleBasedFallback
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample configurations
AWS_BEDROCK_CONFIG = {
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "region": "us-east-1",
    "max_tokens": 2000,
    "temperature": 0.1
}

GOOGLE_VERTEX_CONFIG = {
    "model": "claude-3-5-sonnet@20241022",
    "project_id": "your-gcp-project-id",
    "location": "us-central1",
    "max_tokens": 2000,
    "temperature": 0.1
}

GOOGLE_VERTEX_GEMINI_CONFIG = {
    "model": "gemini-1.5-pro",
    "project_id": "your-gcp-project-id",
    "location": "us-central1",
    "max_tokens": 2000,
    "temperature": 0.1,
    "top_p": 0.8,
    "top_k": 40
}

# Sample security events for testing
SAMPLE_EVENTS = [
    {
        "event_data": {
            "src_ip": "192.168.1.100",
            "dst_ip": "8.8.8.8",
            "event_type": "suspicious_network_connection",
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "medium"
        },
        "user_prompt": "Check if this IP is malicious and investigate the connection"
    },
    {
        "event_data": {
            "hostname": "workstation-01",
            "process_name": "suspicious.exe",
            "event_type": "malware_detection",
            "file_hash": "abc123def456789",
            "severity": "high"
        },
        "user_prompt": "Create a high priority ticket and investigate this endpoint for threats"
    },
    {
        "event_data": {
            "domain": "malicious-site.com",
            "user": "john.doe",
            "event_type": "web_access_blocked",
            "timestamp": "2024-01-15T14:20:00Z"
        },
        "user_prompt": "Analyze this domain reputation and check for other similar incidents"
    }
]

async def demonstrate_gemini_provider():
    """Demonstrate the new Google Vertex AI Gemini provider"""
    print("=" * 60)
    print("Google Vertex AI Gemini Provider Demonstration")
    print("=" * 60)
    
    try:
        # Create Gemini provider
        gemini_provider = GoogleVertexGeminiProvider(GOOGLE_VERTEX_GEMINI_CONFIG)
        
        print(f"✅ Provider created successfully")
        print(f"📋 Configuration: {json.dumps(GOOGLE_VERTEX_GEMINI_CONFIG, indent=2)}")
        
        # Check availability (this will fail without proper GCP setup)
        is_available = gemini_provider.is_available()
        print(f"🔍 Provider available: {is_available}")
        
        if not is_available:
            print("⚠️  Note: Gemini provider not available (requires GCP setup)")
            print("   This is expected in demo mode without GCP credentials")
        
        # Demonstrate each sample event
        for i, sample in enumerate(SAMPLE_EVENTS, 1):
            print(f"\n📝 Sample Event {i}:")
            print(f"   Event: {json.dumps(sample['event_data'], indent=6)}")
            print(f"   Prompt: {sample['user_prompt']}")
            
            try:
                if is_available:
                    result = await gemini_provider.analyze_security_event(
                        sample['event_data'], 
                        sample['user_prompt']
                    )
                    print(f"✅ Analysis Result: {json.dumps(result, indent=6)}")
                else:
                    print("⚠️  Skipping analysis (provider not available)")
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
    
    except Exception as e:
        print(f"❌ Failed to create Gemini provider: {e}")
        print("   This is expected without proper GCP setup")

async def demonstrate_provider_factory():
    """Demonstrate the AI Provider Factory with the new provider"""
    print("\n" + "=" * 60)
    print("AI Provider Factory Demonstration")
    print("=" * 60)
    
    # Configuration for different providers
    ai_configs = [
        {
            "name": "AWS Bedrock",
            "config": {
                "provider": "aws_bedrock",
                "aws_bedrock": AWS_BEDROCK_CONFIG
            }
        },
        {
            "name": "Google Vertex AI (Claude)",
            "config": {
                "provider": "google_vertex",
                "google_vertex": GOOGLE_VERTEX_CONFIG
            }
        },
        {
            "name": "Google Vertex AI (Gemini)",
            "config": {
                "provider": "google_vertex_gemini",
                "google_vertex_gemini": GOOGLE_VERTEX_GEMINI_CONFIG
            }
        }
    ]
    
    for config_info in ai_configs:
        print(f"\n🔧 Testing {config_info['name']} Provider:")
        
        try:
            provider = AIProviderFactory.create_provider(config_info['config'])
            print(f"✅ Provider created: {type(provider).__name__}")
            
            is_available = provider.is_available()
            print(f"🔍 Available: {is_available}")
            
            if not is_available:
                print("⚠️  Provider not available (requires proper credentials)")
                
        except Exception as e:
            print(f"❌ Failed to create provider: {e}")
    
    # Test getting available providers
    print(f"\n📋 Testing get_available_providers:")
    all_config = {
        "aws_bedrock": AWS_BEDROCK_CONFIG,
        "google_vertex": GOOGLE_VERTEX_CONFIG,
        "google_vertex_gemini": GOOGLE_VERTEX_GEMINI_CONFIG
    }
    
    try:
        available_providers = AIProviderFactory.get_available_providers(all_config)
        print(f"✅ Available providers: {available_providers}")
    except Exception as e:
        print(f"❌ Failed to get available providers: {e}")

async def demonstrate_fallback_comparison():
    """Compare the new provider with rule-based fallback"""
    print("\n" + "=" * 60)
    print("Provider vs Fallback Comparison")
    print("=" * 60)
    
    sample_event = SAMPLE_EVENTS[0]  # Use first sample event
    
    print(f"📝 Event Data: {json.dumps(sample_event['event_data'], indent=2)}")
    print(f"💬 User Prompt: {sample_event['user_prompt']}")
    
    # Test rule-based fallback
    print(f"\n🔄 Rule-based Fallback Analysis:")
    try:
        fallback_result = RuleBasedFallback.analyze_security_event(
            sample_event['event_data'],
            sample_event['user_prompt']
        )
        print(f"✅ Fallback Result:")
        print(f"   Actions: {len(fallback_result['actions'])} recommended")
        print(f"   Severity: {fallback_result['severity']}")
        print(f"   Priority: {fallback_result['priority']}")
        print(f"   Reasoning: {fallback_result['reasoning']}")
        
        for action in fallback_result['actions']:
            print(f"   • {action['server']}: {action['action']}")
            
    except Exception as e:
        print(f"❌ Fallback analysis failed: {e}")
    
    # Compare with Gemini provider (if available)
    print(f"\n🤖 Gemini Provider Analysis:")
    try:
        gemini_provider = GoogleVertexGeminiProvider(GOOGLE_VERTEX_GEMINI_CONFIG)
        
        if gemini_provider.is_available():
            gemini_result = await gemini_provider.analyze_security_event(
                sample_event['event_data'],
                sample_event['user_prompt']
            )
            print(f"✅ Gemini Result:")
            print(f"   Actions: {len(gemini_result['actions'])} recommended")
            print(f"   Severity: {gemini_result['severity']}")
            print(f"   Priority: {gemini_result['priority']}")
            print(f"   Reasoning: {gemini_result['reasoning']}")
        else:
            print("⚠️  Gemini provider not available")
            
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")

def demonstrate_configuration_examples():
    """Show different configuration examples for the new provider"""
    print("\n" + "=" * 60)
    print("Configuration Examples")
    print("=" * 60)
    
    configs = {
        "Basic Gemini Configuration": {
            "model": "gemini-1.5-pro",
            "project_id": "my-gcp-project",
            "location": "us-central1"
        },
        "Advanced Gemini Configuration": {
            "model": "gemini-1.5-pro",
            "project_id": "my-gcp-project",
            "location": "us-central1",
            "max_tokens": 4000,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 50
        },
        "Production Gemini Configuration": {
            "model": "gemini-1.5-pro",
            "project_id": "production-project",
            "location": "us-central1",
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40
        }
    }
    
    for name, config in configs.items():
        print(f"\n📋 {name}:")
        print(json.dumps(config, indent=2))

async def main():
    """Main demonstration function"""
    print("🚀 Starting Google Vertex AI Gemini Provider Demonstration")
    print("📝 This demo shows the new provider capabilities and usage")
    
    try:
        await demonstrate_gemini_provider()
        await demonstrate_provider_factory()
        await demonstrate_fallback_comparison()
        demonstrate_configuration_examples()
        
        print("\n" + "=" * 60)
        print("✅ Demonstration completed successfully!")
        print("💡 Key Features of the new Gemini provider:")
        print("   • Native Google Vertex AI integration")
        print("   • Support for Gemini 1.5 Pro model")
        print("   • Advanced generation parameters (top_p, top_k)")
        print("   • Automatic JSON response parsing")
        print("   • Graceful fallback handling")
        print("   • Full compatibility with existing MCP servers")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        logger.exception("Demonstration error")

if __name__ == "__main__":
    asyncio.run(main())
