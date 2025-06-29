#!/usr/bin/env python3
"""
Test script for the bulk research generator.
Tests the generation of research articles for a small subset of instruments.
"""

from generate_bulk_research import BulkResearchGenerator
import os
import sys
import json
import asyncio
from datetime import datetime

# Add the current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


async def test_bulk_research_generation():
    """Test the bulk research generation with a small subset of instruments."""
    print("=" * 60)
    print("TESTING BULK RESEARCH GENERATOR")
    print("=" * 60)

    try:
        # Create generator
        generator = BulkResearchGenerator(
            vector_db_url="http://localhost:6000",
            research_service_url="http://localhost:6283"
        )

        # Limit to first 3 instruments for testing
        original_instruments = generator.instruments
        generator.instruments = original_instruments[:3]

        print(f"Testing with {len(generator.instruments)} instruments:")
        for i, instrument in enumerate(generator.instruments, 1):
            print(f"  {i}. {instrument.get('Instrument_Long_Name', 'Unknown')}")

        print("\nStarting test generation...")

        # Run the generation
        summary = await generator.generate_all_research()

        # Print results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Instruments processed: {summary['total_instruments']}")
        print(f"Total reports generated: {summary['total_reports']}")
        print(f"Successful reports: {summary['successful_reports']}")
        print(f"Failed reports: {summary['failed_reports']}")
        print(f"Reports with desk: {summary['reports_with_desk']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Desk assignment rate: {summary['desk_assignment_rate']:.1f}%")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")

        # Save test summary
        test_summary_file = f"/mcp/test_bulk_research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(test_summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nTest summary saved to: {test_summary_file}")

        if summary['failed_reports'] == 0:
            print("\nTEST PASSED: All research reports generated successfully!")
        else:
            print(
                f"\nTEST WARNING: {summary['failed_reports']} reports failed")

        return summary['failed_reports'] == 0

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bulk_research_generation())
    sys.exit(0 if success else 1)
