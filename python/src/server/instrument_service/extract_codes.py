import json
import os
from typing import Any, Dict


def extract_instrument_codes() -> Dict[str, Any]:
    # Define the path to the instrument_service.json file
    file_path = "./instrument.json"

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return {}

        # Read the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

        # Initialize an empty list to store the results
    results: Dict[str, Any] = {}

    # Extract instrument codes
    for instrument in data:
        name = instrument.get("Instrument_Long_Name", "")

        if name not in results:
            results[name] = []
            # Check for SEDOL
            if "SEDOL" in instrument:
                results[name].append(("SEDOL", instrument["SEDOL"], name))

            # Check for ISIN
            if "ISIN" in instrument:
                results[name].append(("ISIN", instrument["ISIN"], name))

            # Check for Reuters_Code
            if "Reuters_Code" in instrument:
                results[name].append(
                    ("Reuters_Code", instrument["Reuters_Code"], name))
        else:
            print(f"Duplicate instrument found: {name}")

    return results


    # Run the function and print the results
if __name__ == "__main__":
    instrument_codes = extract_instrument_codes()
    for k, v in instrument_codes.items():
        for x in v:
            print(f"{x},")
