import json
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Define constants for clarity
HEADLINE_MAX_LENGTH = 80


class EquityReportGenerator:
    def __init__(self,
                 research_config_json: Dict[str, Any]) -> None:
        """
        Initializes the EquityReportGenerator with data resources.
        
        Args:
            research_config_json (Dict): A dictionary containing sectors,
                                       sentiment data, and event details.
        Raises:
            ValueError: If the input JSON is missing required keys.
        """
        self._data = research_config_json

        required_keys = ["sectors", "sentiment_data",
                         "events", "financial_figures"]
        if not all(key in self._data for key in required_keys):
            missing = [key for key in required_keys if key not in self._data]
            raise ValueError(
                f"Missing required keys in research_config_json: {missing}")

        self._sectors: List[str] = self._data["sectors"]
        self._sentiment_data: Dict[str, Any] = self._data["sentiment_data"]
        self._events: List[Dict[str, Any]] = self._data["events"]
        self._financial_figures: Dict[str, List[str]] = self._data["financial_figures"]

        # Define sentiment distribution as requested (10%, 20%, 40%, 20%, 10%)
        self._sentiment_distribution: Dict[str, float] = {
            "Extremely Negative": 0.10,
            "Negative": 0.20,
            "Neutral": 0.40,
            "Positive": 0.20,
            "Extremely Positive": 0.10
        }

        # Map event types to their sentiment for easy lookup
        self._event_sentiment_map: Dict[str, str] = {
            event['type']: event['sentiment'] for event in self._events}

        # Map sentiment to financial figure types for easier lookup
        self._sentiment_figure_type_map: Dict[str, List[str]] = {
            "Extremely Negative": ["negative", "extremely_negative_volume"],
            "Negative": ["negative_modest", "negative_share_price"],
            "Neutral": ["neutral_share_price", "neutral_volume", "neutral_range",
                        "neutral_revenue", "neutral_market_share", "neutral_valuation"],
            "Positive": ["positive", "positive_revenue", "positive_share_price",
                         "positive_market_share", "positive_valuation"],
            "Extremely Positive": ["extremely_positive", "extremely_positive_earnings",
                                   "extremely_positive_share_price", "extremely_positive_market_share",
                                   "extremely_positive_valuation"]
        }

    def _get_random_sentiment(self) -> str:
        """
        Selects a random sentiment based on the predefined distribution.
        Returns:
            str: A randomly chosen sentiment.
        """
        sentiments = list(self._sentiment_distribution.keys())
        weights = list(self._sentiment_distribution.values())
        return random.choices(sentiments, weights=weights, k=1)[0]

    def _get_financial_figure(self, sentiment_category: str) -> str:
        """
        Selects a random financial figure based on the sentiment category.
        Args:
            sentiment_category (str): The sentiment category.
        Returns:
            str: A randomly chosen financial figure, or an empty string if none found.
        """
        figure_types = self._sentiment_figure_type_map.get(
            sentiment_category, [])
        if not figure_types:
            return ""

        chosen_type = random.choice(figure_types)
        return random.choice(self._financial_figures.get(chosen_type, []))

    def generate_random_analyst(self) -> str:
        """
        Generates a random analyst name using first_name, family_name, and title from the config.
        25% of the time, title will be forced to blank.

        Returns:
            str: A randomly generated full name, with or without title.
        """
        first_name = random.choice(self._data.get("first_names", []))
        family_name = random.choice(self._data.get("family_names", []))

        # 25% chance of having no title
        if random.random() < 0.25:
            title = ""
        else:
            title = random.choice(self._data.get("title", []))

        # Format the full name with or without title
        if title:
            full_name = f"{title} {first_name} {family_name}"
        else:
            full_name = f"{first_name} {family_name}"

        return full_name

    def generate_report(self,
                        stock_name: str,
                        sector: str,
                        venue: str) -> Dict[str, str]:
        """
        Generates a single equity research report.

        Args:
            stock_name (str): The company name.
            sector (str): The industry sector of the stock.
            venue (str): The market/exchange identifier (e.g., NASDAQ, NYSE).

        Returns:
            dict: A JSON object representing the equity research report.
        """
        # Define rating map outside try block so it's available in the return statement
        rating_map = {
            "Extremely Negative": "Strong Sell",
            "Negative": "Sell",
            "Neutral": "Hold",
            "Positive": "Buy",
            "Extremely Positive": "Strong Buy"
        }
        
        try:
            # 1. Determine sentiment (rating)
            chosen_sentiment = self._get_random_sentiment()

            # 2. Filter events by chosen sentiment
            possible_events_for_sentiment = [
                event for event in self._events if event.get('sentiment') == chosen_sentiment
            ]

            event_type = "Financial Update"
            event_description = "General financial performance observations."
            if possible_events_for_sentiment:
                chosen_event = random.choice(possible_events_for_sentiment)
                event_type = chosen_event.get('type', event_type)
                event_description = chosen_event.get(
                    'description', event_description)

            # 3. Get a random financial figure based on sentiment
            financial_figure = self._get_financial_figure(chosen_sentiment)

            # 4. Generate headline (title)
            headline_templates = self._sentiment_data.get(
                chosen_sentiment, {}).get("headlines", [])
            headline = "Equity Research: Company Update"  # Default headline
            if headline_templates:
                headline_template = random.choice(headline_templates)
                try:
                    headline = headline_template.format(
                        stock_name=stock_name,
                        event_type=event_type
                    )
                except KeyError as e:
                    print(
                        f"Warning: Missing key in headline template for sentiment {chosen_sentiment}: {str(e)}")
                    headline = headline_template  # Use template as fallback

            # Ensure headline is punchy and short
            headline = headline[:HEADLINE_MAX_LENGTH] + \
                "..." if len(headline) > HEADLINE_MAX_LENGTH else headline

            # 5. Generate report body
            article_snippets = self._sentiment_data.get(
                chosen_sentiment, {}).get("article_snippets", [])
            combined_article_text = "No research report content available."  # Default

            if article_snippets:
                # Generate a random analyst name for the report
                random_name = self.generate_random_analyst()

                article_template = random.choice(article_snippets)
                format_vars = {
                    "stock_name": stock_name,
                    "sector": sector,
                    "market_id": venue,
                    "event_type": event_type,
                    "name": random_name,  # Add the random name to format variables
                }

                # Add all possible financial figure keys for this sentiment
                figure_types_for_sentiment = self._sentiment_figure_type_map.get(
                    chosen_sentiment, [])
                for fig_type in figure_types_for_sentiment:
                    format_vars[f"financial_figure_{fig_type}"] = financial_figure

                try:
                    # Use **format_vars for cleaner formatting
                    article_text_main = article_template.format(**format_vars)

                    # Add a research summary section
                    rating_map = {
                        "Extremely Negative": "Strong Sell",
                        "Negative": "Sell", 
                        "Neutral": "Hold",
                        "Positive": "Buy",
                        "Extremely Positive": "Strong Buy"
                    }
                    
                    rating = rating_map.get(chosen_sentiment, "Hold")
                    
                    # Create a more structured research report
                    required_elements = [stock_name, venue, sector]
                    random.shuffle(required_elements)
                    
                    report_structure = f"{article_text_main}\n\n"
                    report_structure += f"INVESTMENT SUMMARY: {' '.join(required_elements)}. "
                    report_structure += f"Based on our analysis, we rate {stock_name} as {rating}.\n\n"
                    report_structure += f"ANALYST: {random_name}, Equity Research Division"
                    
                    combined_article_text = report_structure

                except KeyError as e:
                    print(
                        f"Warning: Missing key in article snippet template for sentiment {chosen_sentiment}: {str(e)}")
                    combined_article_text = article_template  # Use template as fallback

            # 6. Generate publish time
            # Random time within the last 30 days for realism
            publish_time = datetime.now() - timedelta(days=random.randint(0, 90),
                                                     hours=random.randint(0, 23),
                                                     minutes=random.randint(0, 59),
                                                     seconds=random.randint(0, 59))
            publish_time_str = publish_time.strftime("%Y-%b-%d %H:%M:%S")

            return {
                "title": ' '.join(headline.split()),
                "report": ' '.join(combined_article_text.split()),
                "publish_date": publish_time_str,
                "rating": rating_map.get(chosen_sentiment, "Hold")
            }
        except Exception as e:
            error_timestamp = datetime.now().strftime("%Y-%b-%d %H:%M:%S")
            print(f"Error during report generation for {stock_name} at {error_timestamp}: {str(e)}")
            return {
                "title": f"Error Generating Research Report for {stock_name}",
                "report": f"An unexpected error occurred during report generation: {str(e)}",
                "publish_date": error_timestamp,
                "rating": "N/A",
                "error": "True"
            }


# Example Usage:
if __name__ == "__main__":
    try:
        with open("python/src/server/equity_research_service/research_config.json", "r") as f:
            data_resources_str = f.read()

            try:
                data_resources_json = json.loads(data_resources_str)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON format in data_resources_json: {str(e)}")

        generator = EquityReportGenerator(data_resources_json)

        report = generator.generate_report(
            "QuantumLeap Dynamics", "Technology", "NYSE")
        print(json.dumps(report))

    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(f"Error: {str(e)}")