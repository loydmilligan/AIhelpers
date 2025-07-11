"""
Context data compression and decompression utilities for storage optimization.

This module provides utilities for compressing large context data to reduce
storage requirements and improve performance when handling AI session contexts.
"""

import json
import zlib
import base64
from typing import Dict, Any, Union, Tuple
import logging

logger = logging.getLogger(__name__)


def compress_context(context_data: Dict[str, Any], compression_level: int = 6) -> bytes:
    """
    Compress context data using zlib compression.
    
    Args:
        context_data: Dictionary containing context data to compress
        compression_level: Compression level (1-9, where 9 is maximum compression)
        
    Returns:
        Compressed data as bytes
        
    Raises:
        ValueError: If context_data is not serializable or compression fails
    """
    try:
        # Convert to JSON string
        json_string = json.dumps(context_data, separators=(',', ':'), ensure_ascii=False)
        
        # Encode to bytes
        data_bytes = json_string.encode('utf-8')
        
        # Compress using zlib
        compressed_data = zlib.compress(data_bytes, level=compression_level)
        
        logger.debug(f"Compressed context from {len(data_bytes)} to {len(compressed_data)} bytes "
                    f"(ratio: {len(compressed_data)/len(data_bytes):.2%})")
        
        return compressed_data
        
    except (TypeError, ValueError, UnicodeEncodeError) as e:
        raise ValueError(f"Failed to compress context data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error during compression: {str(e)}")


def decompress_context(compressed_data: bytes) -> Dict[str, Any]:
    """
    Decompress context data compressed with compress_context.
    
    Args:
        compressed_data: Compressed data as bytes
        
    Returns:
        Original context data as dictionary
        
    Raises:
        ValueError: If decompression or JSON parsing fails
    """
    try:
        # Decompress using zlib
        decompressed_bytes = zlib.decompress(compressed_data)
        
        # Decode from bytes
        json_string = decompressed_bytes.decode('utf-8')
        
        # Parse JSON
        context_data = json.loads(json_string)
        
        logger.debug(f"Decompressed context data successfully")
        
        return context_data
        
    except zlib.error as e:
        raise ValueError(f"Failed to decompress data: {str(e)}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode decompressed data: {str(e)}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from decompressed data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error during decompression: {str(e)}")


def compress_context_to_string(context_data: Dict[str, Any], compression_level: int = 6) -> str:
    """
    Compress context data and return as base64-encoded string.
    
    Useful for storing compressed data in text fields or JSON documents.
    
    Args:
        context_data: Dictionary containing context data to compress
        compression_level: Compression level (1-9, where 9 is maximum compression)
        
    Returns:
        Base64-encoded compressed data as string
        
    Raises:
        ValueError: If compression fails
    """
    try:
        compressed_bytes = compress_context(context_data, compression_level)
        encoded_string = base64.b64encode(compressed_bytes).decode('ascii')
        return encoded_string
    except Exception as e:
        raise ValueError(f"Failed to compress context to string: {str(e)}")


def decompress_context_from_string(compressed_string: str) -> Dict[str, Any]:
    """
    Decompress context data from base64-encoded string.
    
    Args:
        compressed_string: Base64-encoded compressed data
        
    Returns:
        Original context data as dictionary
        
    Raises:
        ValueError: If decompression fails
    """
    try:
        compressed_bytes = base64.b64decode(compressed_string.encode('ascii'))
        return decompress_context(compressed_bytes)
    except Exception as e:
        raise ValueError(f"Failed to decompress context from string: {str(e)}")


def estimate_context_size(context_data: Dict[str, Any]) -> Tuple[int, int, float]:
    """
    Estimate the uncompressed and compressed sizes of context data.
    
    Args:
        context_data: Dictionary containing context data
        
    Returns:
        Tuple of (uncompressed_size, compressed_size, compression_ratio)
        where compression_ratio is compressed_size / uncompressed_size
        
    Raises:
        ValueError: If size estimation fails
    """
    try:
        # Get uncompressed size
        json_string = json.dumps(context_data, separators=(',', ':'), ensure_ascii=False)
        uncompressed_size = len(json_string.encode('utf-8'))
        
        # Get compressed size
        compressed_data = compress_context(context_data)
        compressed_size = len(compressed_data)
        
        # Calculate ratio
        compression_ratio = compressed_size / uncompressed_size if uncompressed_size > 0 else 0
        
        return uncompressed_size, compressed_size, compression_ratio
        
    except Exception as e:
        raise ValueError(f"Failed to estimate context size: {str(e)}")


def optimize_context_for_storage(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize context data structure for better compression.
    
    This function applies various optimizations to improve compression ratios:
    - Remove empty values and whitespace
    - Sort keys for better patterns
    - Normalize string representations
    
    Args:
        context_data: Dictionary containing context data
        
    Returns:
        Optimized context data dictionary
    """
    def clean_value(value):
        """Recursively clean and optimize values."""
        if isinstance(value, dict):
            # Remove empty dicts and None values, sort keys
            cleaned = {k: clean_value(v) for k, v in sorted(value.items()) 
                      if v is not None and v != {} and v != []}
            return cleaned if cleaned else None
        elif isinstance(value, list):
            # Remove empty lists and None values
            cleaned = [clean_value(item) for item in value 
                      if item is not None and item != {} and item != []]
            return cleaned if cleaned else None
        elif isinstance(value, str):
            # Strip whitespace
            return value.strip() if value.strip() else None
        else:
            return value
    
    try:
        optimized = clean_value(context_data)
        return optimized if optimized is not None else {}
    except Exception as e:
        logger.warning(f"Failed to optimize context data: {str(e)}")
        return context_data


def validate_context_size(context_data: Dict[str, Any], max_size_mb: float = 50.0) -> bool:
    """
    Validate that context data is within acceptable size limits.
    
    Args:
        context_data: Dictionary containing context data
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        True if size is acceptable, False otherwise
    """
    try:
        uncompressed_size, _, _ = estimate_context_size(context_data)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        is_valid = uncompressed_size <= max_size_bytes
        
        if not is_valid:
            logger.warning(f"Context size {uncompressed_size / (1024*1024):.2f}MB exceeds "
                          f"limit of {max_size_mb}MB")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Failed to validate context size: {str(e)}")
        return False