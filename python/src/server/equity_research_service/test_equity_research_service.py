import logging
from typing import List, Tuple
import pytest
import enum
import copy
from python.src.server.equity_research_service.equity_research_service import EquityResearchService
from python.src.server.i_mcp_server import IMCPServer
from python.src.server.instrument_service.instrument_service import InstrumentService
from python.src.server.instrument_service.instrument_service import get_instr_tickers

# Configure logging for tests
logger = logging.getLogger("EquityResearchServiceTest")
logging.basicConfig(level=logging.DEBUG)

# Examine instrument.json as part of InstrumentService for these test cases, should stay fixed as DB is checked into git.


class InstrumentsToVerify(enum.Enum):
    ASTRO_ENERGY = "Astro Energy"
    META_PHARMA = "Meta Pharma"
    VERTEX_ENERGY = "Vertex Energy"
    NON_EXISTENT_STOCK = "XXXX Non Existent Stock"


@pytest.fixture(scope="module")
def equity_research_service_instance():
    """
    Pytest fixture to set up the EquityResearchService instance once per test module.
    """
    config = {}
    config[EquityResearchService.ConfigField.DB_NAME.value] = "research_config.json"
    config[EquityResearchService.ConfigField.DB_PATH.value] = "python/src/server/equity_research_service"
    config[EquityResearchService.ConfigField.SERVER_NAME.value] = "TestEquityResearchServicePytest"

    config[IMCPServer.ConfigFields.AUX_DB_NAME.value] = "instrument.json"
    config[IMCPServer.ConfigFields.AUX_DB_PATH.value] = "python/src/server/instrument_service"

    try:
        service = EquityResearchService(logger, config)
        return service
    except EquityResearchService.ErrorLoadingResearchConfig as e:
        logger.error(f"Failed to initialize EquityResearchService for tests: {str(e)}")
        pytest.fail(f"Failed to initialize EquityResearchService: {str(e)}")


def test_get_all_research_field_names(equity_research_service_instance):
    """
    Tests the get_all_research_field_names method.
    """
    result = equity_research_service_instance.get_all_research_field_names()
    logger.info(f"Result from get_all_research_field_names: {result}")
    assert "research_fields" in result
    assert isinstance(result["research_fields"], list)
    expected_fields = [field.value for field in EquityResearchService.ResearchField]
    for field in expected_fields:
        assert field in result["research_fields"], f"Missing field: {field}"


def test_get_research_no_match(equity_research_service_instance):
    """
    Tests get_research with a term that should return no matches (and thus an error).
    """
    stock_name = InstrumentsToVerify.NON_EXISTENT_STOCK.value  # Ensuring it's unlikely to exist
    result = equity_research_service_instance.get_research(stock_name)
    logger.info(f"Result from get_research with '{stock_name}': {result}")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "error" in result[0], f"Expected an error for stock '{stock_name}'"


def test_get_research_multiple_matches(equity_research_service_instance):
    """
    Tests get_research with a term that might return multiple matches (and thus an error).
    """
    stock_name = "(?i).*"
    result = equity_research_service_instance.get_research(stock_name)
    logger.info(f"Result from get_research with '{stock_name}': {result}")
    assert isinstance(result, list)
    assert len(result) > 0
    if not ("error" in result[0] and "Multiple instruments found" in result[0]["error"]):
        logger.warning(
            f"Test for multiple matches with '{stock_name}' did not produce the expected 'Multiple instruments found' error. Result: {result[0]}")
    assert "error" in result[
        0], f"Expected an error or specific research for stock '{stock_name}'"


def test_get_research_specific_match(equity_research_service_instance):
    """
    Tests get_research with a specific term that should ideally return research reports.
    """
    stock_name = InstrumentsToVerify.ASTRO_ENERGY.value  # Assuming this resolves to a single instrument
    results = equity_research_service_instance.get_research(stock_name)
    logger.info(f"Result from get_research with '{stock_name}': {results}")
    assert isinstance(results, list)
    assert len(results) > 0
    if "error" in results:
        logger.warning(
            f"Received error for '{stock_name}': {results[0]['error']}")
    else:
        expected_fields = [field.value for field in EquityResearchService.ResearchField]
        for result in results:
            for field in expected_fields:
                assert field in result, f"Missing field: {field}"


def test_stress_test_research(equity_research_service_instance):
    """
    Tests the research service with all available tickers.
    """
    tickers: List[Tuple[str, str, str]] = get_instr_tickers()
    if not tickers:
        pytest.skip("No instrument tickers available for stress test.")
    logger.info(f"Running stress test with {len(tickers)} tickers.")
    for ticker in tickers:
        stock_name = ticker[2]
        logger.info(f"Testing research retrieval for stock: {stock_name}")
        results = equity_research_service_instance.get_research(stock_name)
        assert isinstance(
            results, list), f"Expected list for stock {stock_name}"
        if not results:
            assert "No research reports returned for stock {stock_name} where name is a valid instrument name."
        else:
            logger.info(
                f"Retrieved {len(results)} research reports for stock {stock_name}.")