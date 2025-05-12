#!/usr/bin/env python3
"""
MCP Server - Model Context Protocol Server Implementation
This server provides tools and resources for AI models to use.

npx @modelcontextprotocol/inspector python ./mcp-server.py 
"""
import argparse
import logging
import signal
import sys
import time
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-server")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=6277, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()

# Parse arguments early to configure the server
args = parse_arguments()

# Create an MCP server with host and port configuration
mcp = FastMCP("Demo", host=args.host, port=args.port)


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    logger.info(f"Adding {a} and {b}")
    return a + b


# Add a multiplication tool
@mcp.tool()
def multiplyX(a: int, b: int) -> int:
    """Multiply two numbers"""
    logger.info(f"Multiplying {a} and {b}")
    return a * b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    logger.info(f"Generating greeting for {name}")
    return f"Hello, {name}!"


# Add a weather resource example
@mcp.resource("weather://{city}")
def get_weather(city: str) -> Dict[str, Any]:
    """Get weather information for a city (demo data)"""
    logger.info(f"Getting weather for {city}")
    # In a real implementation, this would call a weather API
    return {
        "city": city,
        "temperature": 72,
        "conditions": "sunny",
        "humidity": 45
    }


# Add ping resource for MCP Inspector compatibility
@mcp.resource("ping://")
def ping() -> Dict[str, Any]:
    """Ping endpoint for MCP Inspector compatibility"""
    logger.info("Received ping request from MCP Inspector")
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    }


# Add example prompt resource
@mcp.prompt("prompt://example/{topic}")
def get_example_prompt(topic: str) -> str:
    """Get an example prompt for a specific topic"""
    logger.info(f"Generating example prompt for topic: {topic}")
    
    prompts = {
        "coding": "You are an expert programmer with deep knowledge of software development. Please help me implement a binary search algorithm in Python.",
        "math": "You are a mathematics tutor specializing in calculus and algebra. Can you explain how to find the derivative of f(x) = x^3 + 2x^2 - 5x + 7?",
        "writing": "You are a professional writer and editor with expertise in creative writing. I need help crafting an engaging introduction for my short story about time travel."
    }
    
    # Default prompt if topic not found
    default_prompt = f"You are a helpful assistant. Please provide information about {topic}."
    
    return prompts.get(topic.lower(), default_prompt)

def main():
    """Main entry point for the MCP server"""
    # We already parsed arguments at the top level
    # No need to parse them again
    
    # Configure logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Log server startup
    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    
    # Set up signal handlers for the main process
    def signal_handler(sig, frame):
        logger.info("Shutting down MCP server...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the MCP server directly
        # Host and port were already provided at initialization
        mcp.run()
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
