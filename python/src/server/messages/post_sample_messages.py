#!/usr/bin/env python3
"""
Script to post all sample trading messages to the message server.

This script will post all the sample messages (Trading, Operations, Technology) 
to the message server, which will then forward them to the vector database for 
storage and semantic search functionality.

Usage:
    python post_sample_messages.py [--message-host HOST] [--message-port PORT]

Examples:
    # Post to default localhost server
    python post_sample_messages.py
    
    # Post to custom message server
    python post_sample_messages.py --message-host 192.168.1.100 --message-port 5001
"""

import argparse
import sys
import os

# Add the client directory to the path so we can import the sample messages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sample_trading_messages import SampleTradingMessages


def main():
    parser = argparse.ArgumentParser(
        description="Post sample trading messages to message server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--message-host", 
        default="localhost",
        help="Message server host (default: localhost)"
    )
    
    parser.add_argument(
        "--message-port", 
        type=int,
        default=5174,
        help="Message server port (default: 5174)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Sample Trading Messages Posting Tool")
    print("=" * 60)
    
    # Show configuration
    print(f"Configuration:")
    print(f"  Message Server: {args.message_host}:{args.message_port}")
    print(f"  Mode: Message Server (will forward to Vector DB)")
    print()
    
    # Show what will be posted
    total_messages = (
        len(SampleTradingMessages.get_trading_channel_messages()) +
        len(SampleTradingMessages.get_ops_channel_messages()) +
        len(SampleTradingMessages.get_tech_channel_messages())
    )
    
    print(f"Will post {total_messages} messages:")
    print(f"  Trading Channel: {len(SampleTradingMessages.get_trading_channel_messages())} messages")
    print(f"  Operations Channel: {len(SampleTradingMessages.get_ops_channel_messages())} messages")
    print(f"  Technology Channel: {len(SampleTradingMessages.get_tech_channel_messages())} messages")
    print()
    
    # Confirm before proceeding
    try:
        response = input("Proceed with posting? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Cancelled.")
            return 0
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 0
    
    print("\nStarting message posting...")
    print("-" * 40)
    
    try:
        # Post to message server (which forwards to vector database)
        results = SampleTradingMessages.post_all_messages_to_server(
            message_server_host=args.message_host,
            message_server_port=args.message_port
        )
        
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        
        success_rate = (results['total_success'] / total_messages * 100) if total_messages > 0 else 0
        print(f"Overall Success Rate: {success_rate:.1f}% ({results['total_success']}/{total_messages})")
        print()
        
        if results['total_success'] == total_messages:
            print("🎉 ALL MESSAGES POSTED SUCCESSFULLY!")
            print("The sample trading messages have been sent to the message server,")
            print("which will forward them to the vector database for semantic search.")
        elif results['total_success'] > 0:
            print("⚠️  PARTIAL SUCCESS - Some messages were posted successfully")
            print("Check the detailed output above for any failed messages.")
        else:
            print("❌ NO MESSAGES WERE POSTED SUCCESSFULLY")
            print("Please check that the message server is running and accessible:")
            print(f"  - Message Server: http://{args.message_host}:{args.message_port}")
        
        return 0 if results['total_failed'] == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Error during posting: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
