from typing import Dict, List
import datetime
import uuid
import requests
import json
import time


class SampleTradingMessages:
    """
    Class to generate sample chat messages for trading channels based on MCP system data.
    Contains realistic messages using actual staff names, instruments, clients, and brokers.
    """

    # Channel GUIDs
    TRADING_CHANNEL_GUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    OPS_CHANNEL_GUID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"
    TECH_CHANNEL_GUID = "c3d4e5f6-a7b8-9012-cdef-345678901234"

    @staticmethod
    def get_trading_channel_messages() -> List[Dict[str, str]]:
        """Generate sample messages for Trading channel"""
        return [
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Alice Johnson: Just executed 15K shares of Astro Energy at 124.50 via VWAP. Client Ardent Capital Partners looks happy with the fill.",
                "timestamp": "2025-06-28 09:15:23"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Bob Smith: Desk001 seeing heavy flow in Meta Capital today. Reuters showing some positive analyst coverage driving volume.",
                "timestamp": "2025-06-28 09:22:47"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Marcus Thompson: Stonebridge Securities looking for 50K Delta Tech - anyone have liquidity? Need to work this carefully.",
                "timestamp": "2025-06-28 10:05:12"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Charlie Brown: Large block of Alpha Group just crossed at 98.75 - 100K shares via Cascade Ridge Capital. Clean execution.",
                "timestamp": "2025-06-28 11:30:45"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Diana Prince: Nano Pharma hitting new highs - up 3.2% on earnings beat. Seeing good two-way flow from institutional clients.",
                "timestamp": "2025-06-28 12:15:33"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Ethan Hunt: Working large TWAP order for Tidewell Financial Holdings - 75K shares of Meta Capital. Spreading across next 2 hours.",
                "timestamp": "2025-06-28 13:42:18"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Sarah Williams: Monarch Point Investments wants aggressive execution on Delta Tech. Using SNPR algo to minimize market impact.",
                "timestamp": "2025-06-28 14:20:55"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "Fiona Gallagher: Alert: Astro Energy volume spike - 500K shares traded in last 30 mins. Price holding steady around 124.",
                "timestamp": "2025-06-28 15:08:27"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "David Chen: Aquila Asset Markets looking to unwind large Alpha Group position. Need to work this over several sessions.",
                "timestamp": "2025-06-28 15:45:12"
            },
            {
                "channel": SampleTradingMessages.TRADING_CHANNEL_GUID,
                "message": "George Costanza: End of day recap: Desk001 traded $47.3M across 156 tickets. VWAP performance +0.03 bps. Good day team!",
                "timestamp": "2025-06-28 16:30:00"
            }
        ]

    @staticmethod
    def get_ops_channel_messages() -> List[Dict[str, str]]:
        """Generate sample messages for Operations channel"""
        return [
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Lisa Anderson: Settlement exception on trade TRD_42a15724 - Vanguard Stratagem Ltd account missing SWIFT details. Following up with client services.",
                "timestamp": "2025-06-28 09:45:33"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Michael Brown: T+2 settlement batch for Desk002 looks clean. 47 trades totaling $23.5M processed successfully through Cascade Ridge Capital.",
                "timestamp": "2025-06-28 11:18:09"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Jennifer Davis: FYI - Echelon Equities Group requesting trade confirmation PDF for yesterday's Alpha Group block. Sending via secure email.",
                "timestamp": "2025-06-28 08:55:41"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Robert Wilson: Reconciliation complete for Desk005 - all 23 Nano Pharma trades matched with Silverstrand Securities. No breaks to report.",
                "timestamp": "2025-06-28 14:22:15"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Amanda Taylor: Trade break on ORD_d273c17c - quantity mismatch with Orion Summit Markets. Investigating with counterparty.",
                "timestamp": "2025-06-28 10:32:44"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Lisa Anderson: Corporate action processing for Meta Capital dividend - ex-date tomorrow. Updating all open positions.",
                "timestamp": "2025-06-28 12:55:17"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Michael Brown: Cash reconciliation complete for Northgate Trading Co. - $2.3M settlement received from Ironwave Global Brokers.",
                "timestamp": "2025-06-28 13:28:52"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Jennifer Davis: Urgent: Failed trade ORD_67e94617 needs manual intervention. Astro Energy position stuck in limbo with Zephyr Rock Investments.",
                "timestamp": "2025-06-28 14:45:03"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Robert Wilson: Monthly P&L reconciliation in progress. Small discrepancy on Desk007 - investigating with Finance team.",
                "timestamp": "2025-06-28 15:12:36"
            },
            {
                "channel": SampleTradingMessages.OPS_CHANNEL_GUID,
                "message": "Amanda Taylor: All regulatory reporting submitted on time. MiFID II transaction reports for 847 trades processed successfully.",
                "timestamp": "2025-06-28 16:05:21"
            }
        ]

    @staticmethod
    def get_tech_channel_messages() -> List[Dict[str, str]]:
        """Generate sample messages for Technology channel"""
        return [
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Rachel Kim: Market data feed hiccup on Reuters causing 2-second delay in Astro Energy pricing. Failover to backup feed activated.",
                "timestamp": "2025-06-28 10:33:28"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Steven Clark: Deploying algo strategy updates to Desk008 - new ICEBERG parameters for better dark pool interaction. Testing in UAT first.",
                "timestamp": "2025-06-28 13:47:52"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Nicole Wong: Order Management System showing increased latency to Orion Summit Markets. Network team investigating potential routing issue.",
                "timestamp": "2025-06-28 15:12:07"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Brian Liu: Database backup completed successfully. All trading systems operational. Next scheduled maintenance window: Sunday 2AM GMT.",
                "timestamp": "2025-06-28 16:45:12"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Samantha Park: PROD alert: CPU usage spike on trade processing server. Auto-scaling triggered - additional capacity online.",
                "timestamp": "2025-06-28 09:18:45"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Rachel Kim: FIX gateway to Cascade Ridge Capital showing intermittent disconnects. Monitoring connection stability.",
                "timestamp": "2025-06-28 11:25:33"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Steven Clark: Risk management system upgrade scheduled for tonight 8PM. Expect brief interruption to real-time position monitoring.",
                "timestamp": "2025-06-28 12:40:18"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Nicole Wong: Security patch deployment complete on all trading workstations. No trading impact observed during rollout.",
                "timestamp": "2025-06-28 14:05:42"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Brian Liu: Performance optimization on Meta Capital options pricing engine showing 15% latency improvement. Rolling to production.",
                "timestamp": "2025-06-28 15:33:27"
            },
            {
                "channel": SampleTradingMessages.TECH_CHANNEL_GUID,
                "message": "Samantha Park: End-of-day system health check complete. All services green. Trade reconciliation batch jobs starting at 6PM.",
                "timestamp": "2025-06-28 17:00:00"
            }
        ]

    @staticmethod
    def get_all_sample_messages() -> List[Dict[str, str]]:
        """Get all sample messages from all channels combined"""
        all_messages = []
        all_messages.extend(
            SampleTradingMessages.get_trading_channel_messages())
        all_messages.extend(SampleTradingMessages.get_ops_channel_messages())
        all_messages.extend(SampleTradingMessages.get_tech_channel_messages())

        # Sort by timestamp
        all_messages.sort(key=lambda x: x["timestamp"])
        return all_messages

    @staticmethod
    def get_messages_by_channel(channel: str) -> List[Dict[str, str]]:
        """Get messages for a specific channel"""
        channel_map = {
            SampleTradingMessages.TRADING_CHANNEL_GUID: SampleTradingMessages.get_trading_channel_messages,
            SampleTradingMessages.OPS_CHANNEL_GUID: SampleTradingMessages.get_ops_channel_messages,
            SampleTradingMessages.TECH_CHANNEL_GUID: SampleTradingMessages.get_tech_channel_messages,
            # Support legacy string names for backward compatibility
            "Trading": SampleTradingMessages.get_trading_channel_messages,
            "Ops": SampleTradingMessages.get_ops_channel_messages,
            "Tech": SampleTradingMessages.get_tech_channel_messages
        }

        if channel in channel_map:
            return channel_map[channel]()
        else:
            return []

    @staticmethod
    def get_available_channels() -> List[str]:
        """Get list of available channel names"""
        return [
            SampleTradingMessages.TRADING_CHANNEL_GUID,
            SampleTradingMessages.OPS_CHANNEL_GUID,
            SampleTradingMessages.TECH_CHANNEL_GUID
        ]

    @staticmethod
    def get_channel_names() -> Dict[str, str]:
        """Get mapping of channel GUIDs to human-readable names"""
        return {
            SampleTradingMessages.TRADING_CHANNEL_GUID: "Trading",
            SampleTradingMessages.OPS_CHANNEL_GUID: "Operations",
            SampleTradingMessages.TECH_CHANNEL_GUID: "Technology"
        }

    @staticmethod
    def post_all_messages_to_server(message_server_host: str = "localhost",
                                    message_server_port: int = 5000) -> Dict[str, int]:
        """
        Post all sample messages to the message server, which will then send them to the vector database.

        Args:
            message_server_host: Host of the message server
            message_server_port: Port of the message server

        Returns:
            Dictionary with counts of successfully posted messages per channel
        """
        results = {
            "trading_success": 0,
            "ops_success": 0,
            "tech_success": 0,
            "trading_failed": 0,
            "ops_failed": 0,
            "tech_failed": 0,
            "total_success": 0,
            "total_failed": 0
        }

        # Get all message channels and their messages
        channels = [
            ("trading", SampleTradingMessages.TRADING_CHANNEL_GUID,
             SampleTradingMessages.get_trading_channel_messages()),
            ("ops", SampleTradingMessages.OPS_CHANNEL_GUID,
             SampleTradingMessages.get_ops_channel_messages()),
            ("tech", SampleTradingMessages.TECH_CHANNEL_GUID,
             SampleTradingMessages.get_tech_channel_messages())
        ]

        # Post messages to message server (which forwards to vector DB)
        message_server_url = f"http://{message_server_host}:{message_server_port}/send_message"

        for channel_name, channel_guid, messages in channels:
            print(
                f"Posting {len(messages)} messages for {channel_name} channel ({channel_guid})...")

            for message_data in messages:
                try:
                    message_text = message_data["message"]
                    timestamp = message_data["timestamp"]

                    # Post to message server
                    message_payload = {
                        "channel_id": channel_guid,
                        "message": message_text
                    }

                    response = requests.post(
                        message_server_url,
                        json=message_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )

                    # Check if request succeeded
                    if response.status_code in [200, 202]:
                        results[f"{channel_name}_success"] += 1
                        results["total_success"] += 1
                        print(
                            f"✓ Posted message to {channel_name}: {message_text[:50]}...")
                    else:
                        results[f"{channel_name}_failed"] += 1
                        results["total_failed"] += 1
                        print(
                            f"✗ Failed to post message to {channel_name}: {message_text[:50]}...")
                        print(
                            f"  Message server status: {response.status_code}")
                        if response.text:
                            print(f"  Response: {response.text[:100]}")

                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)

                except Exception as e:
                    results[f"{channel_name}_failed"] += 1
                    results["total_failed"] += 1
                    print(
                        f"✗ Exception posting message to {channel_name}: {str(e)}")

        print(f"\nSummary:")
        print(
            f"Total messages posted successfully: {results['total_success']}")
        print(f"Total messages failed: {results['total_failed']}")
        print(
            f"Trading: {results['trading_success']} success, {results['trading_failed']} failed")
        print(
            f"Operations: {results['ops_success']} success, {results['ops_failed']} failed")
        print(
            f"Technology: {results['tech_success']} success, {results['tech_failed']} failed")

        return results

    @staticmethod
    def test_server_connectivity(message_server_host: str = "localhost",
                                 message_server_port: int = 5000) -> Dict[str, bool]:
        """
        Test connectivity to the message server.

        Returns:
            Dictionary indicating whether the message server is accessible
        """
        import requests

        results = {
            "message_server": False,
            "message_server_url": f"http://{message_server_host}:{message_server_port}"
        }

        # Test message server
        try:
            response = requests.get(
                f"http://{message_server_host}:{message_server_port}/", timeout=5)
            results["message_server"] = response.status_code in [
                200, 404]  # 404 is ok, means server is running
        except Exception as e:
            print(f"Message server connectivity test failed: {e}")

        print(f"Server Connectivity Test Results:")
        print(
            f"  Message Server ({results['message_server_url']}): {'✓ Connected' if results['message_server'] else '✗ Not accessible'}")

        return results
