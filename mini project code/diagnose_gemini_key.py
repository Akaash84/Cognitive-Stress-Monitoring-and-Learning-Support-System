"""
Diagnostic tool to verify Gemini API key setup and Streamlit secrets configuration
"""

import os
import sys
from pathlib import Path

def check_env_variable():
    """Check if GEMINI_API_KEY environment variable is set"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("\n📋 Environment Variable Check:")
    print("-" * 60)
    
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 15 else "***"
        print(f"✅ GEMINI_API_KEY found: {masked_key}")
        print(f"   Length: {len(api_key)} characters")
        return True
    else:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("\n   To set it in PowerShell:")
        print("   $env:GEMINI_API_KEY='your-key-here'")
        print("\n   To set it permanently in PowerShell:")
        print("   [Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your-key-here', 'User')")
        return False

def check_secrets_toml():
    """Check if .streamlit/secrets.toml exists and contains the API key"""
    secrets_path = Path(".streamlit/secrets.toml")
    
    print("\n📋 Secrets.toml File Check:")
    print("-" * 60)
    
    if not secrets_path.exists():
        print("❌ .streamlit/secrets.toml file not found")
        print("\n   Create it at: .streamlit/secrets.toml")
        print("\n   Content should be:")
        print("   ```toml")
        print("   GEMINI_API_KEY = \"your-actual-api-key-here\"")
        print("   ```")
        return False
    
    print("✅ .streamlit/secrets.toml file found")
    
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "GEMINI_API_KEY" in content:
            print("✅ GEMINI_API_KEY is defined in secrets.toml")
            
            # Check if value looks valid (has = and quotes or value)
            if '=' in content and 'GEMINI_API_KEY' in content:
                # Try to extract the value
                lines = content.split('\n')
                for line in lines:
                    if 'GEMINI_API_KEY' in line and not line.strip().startswith('#'):
                        print(f"\n   Line: {line}")
                        
                        # Check for proper format
                        if '=' not in line:
                            print("   ⚠️  Format issue: Missing '=' sign")
                            return False
                        
                        value_part = line.split('=', 1)[1].strip()
                        
                        if not value_part:
                            print("   ⚠️  Value is empty!")
                            return False
                        
                        # Remove quotes if present
                        if (value_part.startswith('"') and value_part.endswith('"')) or \
                           (value_part.startswith("'") and value_part.endswith("'")):
                            actual_key = value_part[1:-1]
                        else:
                            actual_key = value_part
                        
                        if actual_key and len(actual_key) > 5:
                            masked = actual_key[:10] + "..." + actual_key[-4:] if len(actual_key) > 15 else "***"
                            print(f"   ✅ Value detected: {masked}")
                            print(f"   ✅ Length: {len(actual_key)} characters")
                            return True
                        else:
                            print(f"   ⚠️  Value looks too short or invalid: '{actual_key}'")
                            return False
        else:
            print("❌ GEMINI_API_KEY not found in secrets.toml")
            print("\n   Add this line to your .streamlit/secrets.toml:")
            print("   GEMINI_API_KEY = \"your-api-key-here\"")
            return False
            
    except Exception as e:
        print(f"❌ Error reading secrets.toml: {e}")
        return False

def check_streamlit_access():
    """Check if Streamlit can access secrets properly"""
    print("\n📋 Streamlit Secrets Access Check:")
    print("-" * 60)
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Check if we're in a Streamlit context
        if not hasattr(st, 'secrets'):
            print("⚠️  st.secrets not available (might be outside Streamlit context)")
            print("    This is normal if running outside of 'streamlit run'")
            return None
        
        if st.secrets:
            print("✅ st.secrets is accessible")
            
            # Try to get the key
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                masked = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 15 else "***"
                print(f"✅ GEMINI_API_KEY accessible via st.secrets: {masked}")
                return True
            else:
                print("❌ GEMINI_API_KEY not found via st.secrets.get()")
                print(f"   Available keys: {list(st.secrets.keys())}")
                return False
        else:
            print("⚠️  st.secrets is empty")
            return False
            
    except ImportError:
        print("❌ Streamlit not installed")
        return False
    except Exception as e:
        print(f"⚠️  Error accessing Streamlit secrets: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("🔍 GEMINI API KEY DIAGNOSTIC TOOL")
    print("="*60)
    
    env_ok = check_env_variable()
    secrets_ok = check_secrets_toml()
    streamlit_ok = check_streamlit_access()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if env_ok:
        print("✅ Environment variable GEMINI_API_KEY is set")
    elif secrets_ok:
        print("✅ API key is in .streamlit/secrets.toml (will work with 'streamlit run')")
    else:
        print("❌ API key not found in any location")
        print("\nFIX THIS NOW:")
        print("\nOption 1: Environment Variable (Use anywhere)")
        print("-" * 60)
        print("PowerShell:")
        print('  $env:GEMINI_API_KEY="sk-..."')
        print("\nThen restart your terminal/app.")
        
        print("\nOption 2: Secrets File (Use with 'streamlit run')")
        print("-" * 60)
        print("1. Create file: .streamlit/secrets.toml")
        print("2. Add line: GEMINI_API_KEY = \"sk-...\"")
        print("3. Save file")
        print("4. Restart Streamlit app")
        
        return 1
    
    if streamlit_ok is False:
        print("⚠️  Streamlit secrets access failed - ensure you're running with 'streamlit run'")
    
    print("\n✅ Setup looks good! Try running your app again.")
    print("="*60 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
