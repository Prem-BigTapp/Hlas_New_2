#!/usr/bin/env python3
"""
Redis Initialization Script
===========================

Checks the connection to the Redis server.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import redis
from redis.exceptions import ConnectionError

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

def check_redis_connection():
    """
    Connects to Redis and checks the connection.
    """
    print("--- Redis Connection Check ---")
    
    try:
        # Connect to Redis
        print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT} (DB: {REDIS_DB})...")
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        
        # Check connection
        r.ping()
        print("✅ Redis connection successful.")
        
        # Set a test key
        r.set("redis_init_check", "success")
        print("✅ Successfully set test key.")
        
        # Get the test key
        val = r.get("redis_init_check")
        if val == "success":
            print("✅ Successfully retrieved test key.")
        else:
            print("❌ Failed to retrieve test key.")
            
        # Clean up
        r.delete("redis_init_check")
        
    except ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Please ensure that your Redis server is running and that the REDIS_HOST/REDIS_PORT in your .env file are correct.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if 'r' in locals() and r:
            r.close()
            print("\nRedis connection closed.")

if __name__ == "__main__":
    check_redis_connection()