"""HTTPX Client with connection pooling"""
import httpx

_client = None

def get_httpx_client(timeout=30.0):
    """Get shared httpx client"""
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    return _client
