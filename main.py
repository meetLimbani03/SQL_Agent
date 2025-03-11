#!/usr/bin/env python3
"""
Main entry point for SQL Agent application
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    return True

def main():
    """Main function"""
    if not check_environment():
        sys.exit(1)
    
    print("Starting SQL Agent Streamlit app...")
    os.system("streamlit run app.py")

if __name__ == "__main__":
    main()