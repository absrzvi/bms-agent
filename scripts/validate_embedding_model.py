#!/usr/bin/env python3
"""
Validate Qwen3 Embedding Model Availability

This script verifies that the Qwen3-Embedding-8B:F16 model is available in Ollama
and returns 4096-dimensional embeddings.

Task: T001
Feature: 004-migrate-qdrant-collection
"""

import argparse
import json
import logging
import requests
import sys
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
EXPECTED_DIMENSION = 4096


def check_ollama_service() -> bool:
    """
    Check if Ollama service is running and accessible.

    Returns:
        bool: True if Ollama is running, False otherwise
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            logger.info(f"Ollama service running: version {version_info.get('version', 'unknown')}")
            return True
        else:
            logger.error(f"Ollama service responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to Ollama service: {e}")
        return False


def check_model_exists(model_name: str) -> bool:
    """
    Check if the specified model exists in Ollama.

    Args:
        model_name: Name of the model to check (e.g., "dengcao/Qwen3-Embedding-8B:F16")

    Returns:
        bool: True if model exists, False otherwise
    """
    try:
        # Use Ollama API to list models
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]

            # Check if our model is in the list
            if model_name in model_names:
                logger.info(f"Model '{model_name}' found in Ollama")
                return True
            else:
                logger.error(f"Model '{model_name}' not found. Available models: {model_names}")
                return False
        else:
            logger.error(f"Failed to list models: status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking model existence: {e}")
        return False


def generate_test_embedding(model_name: str) -> Dict[str, Any]:
    """
    Generate a test embedding using the specified model.

    Args:
        model_name: Name of the model to use

    Returns:
        dict: Result dictionary with 'success', 'dimension', 'latency_ms', 'error'
    """
    test_query = "This is a test query for embedding validation"

    try:
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": model_name, "prompt": test_query},
            timeout=10
        )
        latency_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result = response.json()
            embedding = result.get('embedding', [])
            dimension = len(embedding)

            logger.info(f"Generated test embedding: {dimension} dimensions, {latency_ms:.2f}ms")

            return {
                'success': True,
                'dimension': dimension,
                'latency_ms': latency_ms,
                'error': None
            }
        else:
            error_msg = f"Ollama returned status {response.status_code}: {response.text}"
            logger.error(error_msg)
            return {
                'success': False,
                'dimension': 0,
                'latency_ms': latency_ms,
                'error': error_msg
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate embedding: {e}")
        return {
            'success': False,
            'dimension': 0,
            'latency_ms': 0,
            'error': str(e)
        }


def validate_embedding_dimension(dimension: int) -> bool:
    """
    Validate that the embedding dimension matches expected value.

    Args:
        dimension: Actual dimension from test embedding

    Returns:
        bool: True if dimension matches expected (4096), False otherwise
    """
    if dimension == EXPECTED_DIMENSION:
        logger.info(f"✓ Embedding dimension correct: {dimension}")
        return True
    else:
        logger.error(f"✗ Embedding dimension mismatch: expected {EXPECTED_DIMENSION}, got {dimension}")
        return False


def main() -> int:
    """
    Main validation function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Validate Qwen3 embedding model availability")
    parser.add_argument(
        '--model',
        type=str,
        default='dengcao/Qwen3-Embedding-8B:F16',
        help='Ollama model name to validate'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Optional JSON output file path'
    )
    args = parser.parse_args()

    logger.info(f"Starting embedding model validation for: {args.model}")

    # Step 1: Check Ollama service
    if not check_ollama_service():
        logger.error("FAIL: Ollama service not running")
        return 1

    # Step 2: Check model exists
    if not check_model_exists(args.model):
        logger.error(f"FAIL: Model '{args.model}' not found in Ollama")
        return 1

    # Step 3: Generate test embedding
    result = generate_test_embedding(args.model)
    if not result['success']:
        logger.error(f"FAIL: Could not generate test embedding: {result['error']}")
        return 1

    # Step 4: Validate dimension
    if not validate_embedding_dimension(result['dimension']):
        logger.error("FAIL: Embedding dimension validation failed")
        return 1

    # Step 5: Check latency
    if result['latency_ms'] > 5000:
        logger.warning(f"WARNING: Embedding latency high: {result['latency_ms']:.2f}ms (>5s threshold)")

    # Success summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUCCESSFUL ✓")
    logger.info(f"Model: {args.model}")
    logger.info(f"Dimension: {result['dimension']}")
    logger.info(f"Latency: {result['latency_ms']:.2f}ms")
    logger.info("=" * 60)

    # Optional: Write JSON output
    if args.output:
        output_data = {
            'model_name': args.model,
            'validation_status': 'success',
            'dimension': result['dimension'],
            'latency_ms': result['latency_ms'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Results written to: {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
