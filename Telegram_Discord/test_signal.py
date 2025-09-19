#!/usr/bin/env python3
"""Test Signal integration"""

import os, json
from dotenv import load_dotenv
from src.utils.signal_client import SignalSender
from src.utils.logger import setup_logger

def main():
    load_dotenv()
    
    logger = setup_logger("signal_test", "signal_test.log")
    sender = SignalSender(logger=logger)
    
    # Test data
    test_data = {
        "text": "🔥 **Test Signal Pick** 🔥\n\n**DuckInvestments**\nLakers ML -150 (2u)\nWarriors +5.5 -110 (1.5u)\n\nBOL! 🍀",
        "chat_title": "Test Channel",
        "sender_name": "TestBot",
        "timestamp": "2025-09-19"
    }
    
    # Get recipient from environment or prompt
    recipient = os.getenv("SIGNAL_TEST_RECIPIENT")
    if not recipient:
        print("Set SIGNAL_TEST_RECIPIENT in .env (phone number like +1234567890 or group ID like group.abc123)")
        return
        
    try:
        print(f"Testing Signal message to: {recipient}")
        
        # Format message
        formatted = sender.format_telegram_message(test_data)
        print(f"Formatted message:\n{formatted}\n")
        
        # Send message
        result = sender.send_message(recipient, formatted)
        
        if result:
            print("✅ Signal test message sent successfully!")
        else:
            print("❌ Signal test failed")
            
    except Exception as e:
        print(f"❌ Signal test error: {e}")
        logger.error(f"Signal test failed: {e}")

if __name__ == "__main__":
    main()