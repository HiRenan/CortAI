import sys
import os
import time
import logging
import shutil

# Add backend to sys.path
# Assuming this script is in backend/tests/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.collector_streams import executar_agente_coletor
from src.agents.transcriber import executar_transcricao_segmento
from src.agents.analyst import executar_agente_analista

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_pipeline")

def test_pipeline():
    logger.info("=== Starting Full Pipeline Test ===")
    
    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    output_dir = os.path.join(base_dir, "data", "test_segments")
    
    # 1. Test Collector
    logger.info("\n--- Testing Collector Agent ---")
    # Use Big Buck Bunny HLS stream
    stream_url = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
    
    # Clean up previous test run
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Run collector for a short duration (e.g., 15 seconds, 5s segments)
    # We need enough time to get at least one valid segment
    logger.info(f"Collecting from {stream_url} to {output_dir}")
    result_collector = executar_agente_coletor(
        stream_url=stream_url,
        output_dir=output_dir,
        segment_duration=5,
        max_duration=15
    )
    
    if not result_collector or result_collector['status'] != 'sucesso':
        logger.error("Collector failed!")
        return
    
    logger.info("Collector success!")
    segment_paths = result_collector['segment_paths']
    if not segment_paths:
        logger.error("No segments found!")
        return
        
    first_segment = segment_paths[0]
    logger.info(f"First segment: {first_segment}")
    
    # 2. Test Transcriber
    logger.info("\n--- Testing Transcriber Agent ---")
    result_transcriber = executar_transcricao_segmento(first_segment)
    
    if not result_transcriber or result_transcriber['status'] != 'sucesso':
        logger.error("Transcriber failed!")
        return
        
    logger.info("Transcriber success!")
    transcription_path = result_transcriber['transcription_path']
    logger.info(f"Transcription path: {transcription_path}")
    
    # 3. Test Analyst
    logger.info("\n--- Testing Analyst Agent ---")
    output_analysis_path = transcription_path.replace(".json", "_analysis.json")
    
    try:
        result_analyst = executar_agente_analista(
            input_json=transcription_path,
            output_json=output_analysis_path
        )
        
        logger.info("Analyst success!")
        logger.info(f"Result: {result_analyst}")
        
    except Exception as e:
        logger.error(f"Analyst failed: {e}")
        import traceback
        traceback.print_exc()
        return

    logger.info("\n=== Full Pipeline Test Completed Successfully ===")

if __name__ == "__main__":
    test_pipeline()
