#!/usr/bin/env python3
"""
Script to generate bulk research articles for all instruments and send them to the vector database.
Generates 3 research articles per instrument, with document_type="research" and desk="" except for 25% 
of articles which get a random desk (Desk001...Desk009).

This script calls the Equity Research Service via MCP tool calls instead of importing it directly.
"""

from mcp_client import MCPClient
import json
import os
import sys
import random
import requests
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Add the parent directories to the path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
great_grandparent_dir = os.path.dirname(grandparent_dir)

sys.path.insert(0, great_grandparent_dir)
sys.path.insert(0, grandparent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import MCP client for calling equity research service
sys.path.insert(0, os.path.join(great_grandparent_dir, "client"))


class BulkResearchGenerator:
    """Generates bulk research articles for all instruments and sends them to vector database."""

    # Desk001 to Desk009
    DESK_OPTIONS = [f"Desk{str(i).zfill(3)}" for i in range(1, 10)]
    DESK_PROBABILITY = 0.25  # 25% chance of assigning a desk
    REPORTS_PER_INSTRUMENT = 3

    def __init__(self, vector_db_url: str = "http://localhost:6000", research_service_url: str = "http://localhost:6283"):
        """
        Initialize the bulk research generator.

        Args:
            vector_db_url: URL of the vector database service
            research_service_url: URL of the equity research MCP service
        """
        self.vector_db_url = vector_db_url
        self.research_service_url = research_service_url
        self.logger = self._setup_logger()

        # Load instruments
        self.instruments = self._load_instruments()

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the script."""
        logger = logging.getLogger("BulkResearchGenerator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def _call_research_service(self, stock_name: str) -> List[Dict[str, Any]]:
        try:
            async with MCPClient([self.research_service_url]) as client:
                # Call the get_research tool
                result = await client.execute_tool(
                    server_name="EquityResearch",
                    tool_name="get_research",
                    arguments={"stock_name": f"^{stock_name}$"}
                )

                # Extract the results from MCP response
                if "results" in result and len(result["results"]) > 0:
                    for result_item in result["results"]:
                        if "response" in result_item:
                            return result_item["response"]
                        elif "error" in result_item:
                            self.logger.error(
                                f"MCP error calling research service: {result_item['error']}")
                            return [{"error": result_item["error"]}]

                self.logger.warning(
                    f"No results returned from research service for {stock_name}")
                return [{"error": "No results returned from research service"}]

        except Exception as e:
            self.logger.error(f"Failed to call research service via MCP: {e}")
            return [{"error": f"MCP call failed: {str(e)}"}]

    def _load_instruments(self) -> List[Dict[str, Any]]:
        """Load instruments from instrument.json."""
        # Look for instrument.json in multiple locations
        instrument_paths = [
            "/mcp/python/src/server/instrument_service/instrument.json"
        ]

        instrument_path = None
        for path in instrument_paths:
            if os.path.exists(path):
                instrument_path = path
                break

        if not instrument_path:
            raise FileNotFoundError(
                f"Instrument file not found. Tried: {instrument_paths}")

        self.logger.info(f"Loading instruments from: {instrument_path}")

        with open(instrument_path, 'r', encoding='utf-8') as f:
            instruments = json.load(f)

        self.logger.info(f"Loaded {len(instruments)} instruments")
        return instruments

    def _get_random_desk(self) -> str:
        """
        Get a random desk assignment based on probability.

        Returns:
            Empty string 75% of the time, random desk 25% of the time
        """
        if random.random() < self.DESK_PROBABILITY:
            return random.choice(self.DESK_OPTIONS)
        return ""

    def _send_to_vector_db(self, document: str, desk: str = "") -> bool:
        """
        Send a document to the vector database.

        Args:
            document: The research article text to send
            desk: The desk assignment (empty string or DeskXXX)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.vector_db_url}/add_document"

        payload = {
            "document": document,
            "document_type": "research",
            "desk": desk
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            self.logger.debug(
                f"Successfully sent document to vector DB (desk: '{desk}', response: {response.status_code})")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send document to vector DB: {e}")
            return False

    async def generate_research_for_instrument(self, instrument: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate research articles for a single instrument.

        Args:
            instrument: Instrument data dictionary

        Returns:
            List of generated articles with metadata
        """
        instrument_name = instrument.get("Instrument_Long_Name", "Unknown")
        industry = instrument.get("Industry", "General")

        self.logger.info(
            f"Generating {self.REPORTS_PER_INSTRUMENT} research reports for {instrument_name} (Industry: {industry})")

        articles = []

        # Generate reports by calling get_research multiple times to get exactly 3 reports
        for i in range(self.REPORTS_PER_INSTRUMENT):
            try:
                self.logger.debug(
                    f"  Generating research report {i+1}/{self.REPORTS_PER_INSTRUMENT} for {instrument_name}")

                # Call get_research via MCP to generate reports for this instrument
                research_reports = await self._call_research_service(instrument_name)

                if not research_reports or "error" in research_reports[0]:
                    error_msg = research_reports[0].get(
                        "error", "Unknown error") if research_reports else "No reports generated"
                    self.logger.warning(
                        f"  ✗ Failed to generate research for {instrument_name}: {error_msg}")
                    articles.append({
                        "instrument": instrument_name,
                        "title": "ERROR",
                        "desk": "",
                        "success": False,
                        "report_number": i + 1,
                        "error": error_msg
                    })
                    continue

                # Take the first report (get_research generates 1-3 reports randomly)
                report = research_reports[0] if research_reports else None
                if not report:
                    self.logger.warning(
                        f"  ✗ No research report generated for {instrument_name}")
                    articles.append({
                        "instrument": instrument_name,
                        "title": "ERROR",
                        "desk": "",
                        "success": False,
                        "report_number": i + 1,
                        "error": "No report data"
                    })
                    continue

                # Extract report data
                title = report.get("title", "Untitled Research Report")
                report_text = report.get("report", "")
                publish_date = report.get(
                    "publish_date", datetime.now().isoformat())
                rating = report.get("rating", "N/A")

                self.logger.debug(
                    f"  Generated research title: {title[:60]}...")

                # Create the full document text
                full_document = f"TITLE: {title}\n\nRATING: {rating}\n\nREPORT: {report_text}\n\nPUBLISH_DATE: {publish_date}"

                # Determine desk assignment
                desk = self._get_random_desk()

                # Send to vector database
                self.logger.debug(
                    f"  Sending research report {i+1} to vector DB (desk: '{desk}', doc length: {len(full_document)} chars)")
                success = self._send_to_vector_db(full_document, desk)

                article_info = {
                    "instrument": instrument_name,
                    "title": title,
                    "rating": rating,
                    "desk": desk,
                    "success": success,
                    "report_number": i + 1
                }

                articles.append(article_info)

                if success:
                    desk_info = f" (desk: {desk})" if desk else " (no desk)"
                    self.logger.info(
                        f"  ✓ Research report {i+1}/{self.REPORTS_PER_INSTRUMENT} sent successfully{desk_info}")
                else:
                    self.logger.warning(
                        f"  ✗ Research report {i+1}/{self.REPORTS_PER_INSTRUMENT} failed to send")

            except Exception as e:
                self.logger.error(
                    f"  ✗ Failed to generate research report {i+1} for {instrument_name}: {e}")
                articles.append({
                    "instrument": instrument_name,
                    "title": "ERROR",
                    "desk": "",
                    "success": False,
                    "report_number": i + 1,
                    "error": str(e)
                })

        # Log summary for this instrument
        successful_count = sum(1 for a in articles if a["success"])
        with_desk_count = sum(
            1 for a in articles if a["success"] and a["desk"])
        self.logger.info(
            f"Completed {instrument_name}: {successful_count}/{len(articles)} reports successful, {with_desk_count} with desk assignment")

        return articles

    async def generate_all_research(self) -> Dict[str, Any]:
        """
        Generate research articles for all instruments.

        Returns:
            Summary statistics of the generation process
        """
        self.logger.info("=" * 60)
        self.logger.info(f"STARTING BULK RESEARCH GENERATION")
        self.logger.info(
            f"Total instruments to process: {len(self.instruments)}")
        self.logger.info(
            f"Research reports per instrument: {self.REPORTS_PER_INSTRUMENT}")
        self.logger.info(
            f"Expected total reports: {len(self.instruments) * self.REPORTS_PER_INSTRUMENT}")
        self.logger.info(
            f"Desk assignment probability: {self.DESK_PROBABILITY * 100}%")
        self.logger.info(f"Vector DB URL: {self.vector_db_url}")
        self.logger.info(f"Research Service URL: {self.research_service_url}")
        self.logger.info("=" * 60)

        total_reports = 0
        successful_reports = 0
        failed_reports = 0
        reports_with_desk = 0

        start_time = datetime.now()

        for idx, instrument in enumerate(self.instruments, 1):
            instrument_name = instrument.get("Instrument_Long_Name", "Unknown")

            # Progress indicator
            progress_percent = (idx / len(self.instruments)) * 100
            self.logger.info(
                f"[{idx}/{len(self.instruments)}] ({progress_percent:.1f}%) Processing: {instrument_name}")

            articles = await self.generate_research_for_instrument(instrument)

            # Update statistics
            for article in articles:
                total_reports += 1
                if article["success"]:
                    successful_reports += 1
                    if article["desk"]:
                        reports_with_desk += 1
                else:
                    failed_reports += 1

            # Log running totals every 10 instruments or at the end
            if idx % 10 == 0 or idx == len(self.instruments):
                elapsed = datetime.now() - start_time
                rate = idx / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                self.logger.info(f"Progress Update: {idx}/{len(self.instruments)} instruments processed "
                                 f"({successful_reports} successful, {failed_reports} failed reports) "
                                 f"- Rate: {rate:.1f} instruments/min")

        end_time = datetime.now()
        duration = end_time - start_time

        summary = {
            "total_instruments": len(self.instruments),
            "total_reports": total_reports,
            "successful_reports": successful_reports,
            "failed_reports": failed_reports,
            "reports_with_desk": reports_with_desk,
            "reports_without_desk": successful_reports - reports_with_desk,
            "desk_assignment_rate": (reports_with_desk / successful_reports * 100) if successful_reports > 0 else 0,
            "success_rate": (successful_reports / total_reports * 100) if total_reports > 0 else 0,
            "duration_seconds": duration.total_seconds(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

        self.logger.info("=" * 60)
        self.logger.info("BULK RESEARCH GENERATION COMPLETED")
        self.logger.info("=" * 60)
        self.logger.info(
            f"Total instruments processed: {summary['total_instruments']}")
        self.logger.info(
            f"Total research reports generated: {summary['total_reports']}")
        self.logger.info(
            f"Successful reports: {summary['successful_reports']}")
        self.logger.info(f"Failed reports: {summary['failed_reports']}")
        self.logger.info(
            f"Reports with desk assignment: {summary['reports_with_desk']}")
        self.logger.info(
            f"Reports without desk assignment: {summary['reports_without_desk']}")
        self.logger.info(
            f"Desk assignment rate: {summary['desk_assignment_rate']:.1f}%")
        self.logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        self.logger.info(
            f"Total duration: {summary['duration_seconds']:.2f} seconds")
        self.logger.info(
            f"Average time per instrument: {summary['duration_seconds']/summary['total_instruments']:.2f} seconds")
        self.logger.info(
            f"Average time per report: {summary['duration_seconds']/summary['total_reports']:.2f} seconds")
        self.logger.info("=" * 60)

        return summary


async def async_main():
    """Async main function to run the bulk research generation."""
    # Parse command line arguments for vector DB URL if provided
    vector_db_url = "http://localhost:6000"
    research_service_url = "http://localhost:6283"

    if len(sys.argv) > 1:
        vector_db_url = sys.argv[1]
    if len(sys.argv) > 2:
        research_service_url = sys.argv[2]

    print("=" * 60)
    print("BULK RESEARCH ARTICLE GENERATOR")
    print("=" * 60)
    print(f"Vector DB URL: {vector_db_url}")
    print(f"Research Service URL: {research_service_url}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        generator = BulkResearchGenerator(
            vector_db_url=vector_db_url,
            research_service_url=research_service_url
        )
        summary = await generator.generate_all_research()

        # Save summary to file
        summary_file = f"/mcp/bulk_research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")

        if summary['failed_reports'] > 0:
            print(
                f"\nWarning: {summary['failed_reports']} research reports failed to generate/send")
            print(f"Overall success rate: {summary['success_rate']:.1f}%")
            sys.exit(1)
        else:
            print(
                f"\nSuccess: All {summary['successful_reports']} research reports generated and sent successfully!")
            print(
                f"Desk assignment rate: {summary['desk_assignment_rate']:.1f}% (target: 25%)")

    except Exception as e:
        print(f"\nError running bulk research generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function to run the bulk research generation."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
