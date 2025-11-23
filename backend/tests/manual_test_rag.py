import sys
import os
import json
import logging

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.analyst import AnalystAgent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("manual_test_rag")

def test_rag():
    logger.info("=== Starting Manual RAG Test ===")
    
    # Define paths
    base_dir = os.path.dirname(__file__)
    input_json = os.path.join(base_dir, "dummy_transcription.json")
    
    if not os.path.exists(input_json):
        logger.error(f"Input file not found: {input_json}")
        return

    try:
        # Initialize Agent
        logger.info("Initializing AnalystAgent...")
        agent = AnalystAgent()
        
        # Run Agent
        logger.info(f"Running analysis on {input_json}...")
        result = agent.run(input_json)
        
        logger.info("=== Test Result ===")
        logger.info(json.dumps(result, indent=4, ensure_ascii=False))
        
        # Basic assertions
        if result["highlight_fim_segundos"] > result["highlight_inicio_segundos"]:
             logger.info("SUCCESS: Valid time range detected.")
        else:
             logger.error("FAILURE: Invalid time range.")
             
        if result["resposta_bruta"]:
            logger.info("SUCCESS: Summary generated.")
        else:
            logger.error("FAILURE: No summary generated.")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag()
