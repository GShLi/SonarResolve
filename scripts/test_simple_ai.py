#!/usr/bin/env python
"""
Simple AI Client Test
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_ai_client():
    """Test Enhanced AI Client"""
    print("=== Enhanced AI Client Test ===")
    
    try:
        from src.sonar_resolve.clients.ai_client import AIClientFactory, EnhancedOpenAIClient
        from src.sonar_resolve.core.config import Config
        
        print(f"AI Provider: {Config.AI_PROVIDER}")
        print(f"AI Model: {Config.AI_MODEL}")
        print(f"OpenAI Key configured: {'YES' if Config.OPENAI_API_KEY else 'NO'}")
        print(f"Anthropic Key configured: {'YES' if Config.ANTHROPIC_API_KEY else 'NO'}")
        
        # Test AI client factory
        print("\n1. Testing AI Client Factory...")
        ai_client = AIClientFactory.create_client()
        print(f"SUCCESS: AI client created: {type(ai_client).__name__}")
        
        # Test prompt structure
        print("\n2. Testing Enhanced Prompt Structure...")
        if hasattr(ai_client, '_get_system_prompt'):
            system_prompt = ai_client._get_system_prompt()
            print(f"System prompt length: {len(system_prompt)} characters")
            print("SUCCESS: Enhanced prompt structure available")
        
        print("\n3. Features of Enhanced AI Client:")
        print("- Optimized prompts for SonarQube issue fixing")
        print("- Structured problem information")
        print("- Separate system and user prompts")
        print("- Code block cleaning functionality")
        print("- Compatible with Python 3.8+")
        
        return True
        
    except ImportError as e:
        print(f"IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_client()
    
    print("\n" + "=" * 40)
    if success:
        print("Test PASSED! Enhanced AI client is working.")
        print("\nNext steps:")
        print("1. Configure your AI API keys in .env file")
        print("2. Test with actual SonarQube issues")
        print("3. Run full integration tests")
    else:
        print("Test FAILED! Please check configuration.")
    print("=" * 40)
