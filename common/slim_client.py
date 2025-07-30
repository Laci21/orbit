"""SLIM client helper for inter-agent communication."""

import asyncio
import logging
from typing import Dict, Any

from agntcy_app_sdk.factory import GatewayFactory
from a2a.types import SendMessageRequest, MessageSendParams, Message, TextPart, Role

logger = logging.getLogger("orbit.slim_client")


class SlimClient:
    """Helper class for making SLIM-based A2A calls to other agents."""
    
    def __init__(self):
        self.factory = GatewayFactory()
        self._clients = {}  # Cache clients by agent_url
    
    def _convert_jsonrpc_to_a2a(self, jsonrpc_request: Dict[str, Any]) -> SendMessageRequest:
        """Convert JSON-RPC request to A2A SendMessageRequest format."""
        params = jsonrpc_request.get("params", {})
        message_data = params.get("message", {})
        
        # Extract message parts and convert to TextPart objects
        parts = []
        for part in message_data.get("parts", []):
            if part.get("type") == "text" or part.get("kind") == "text":
                text_part = TextPart(text=part.get("text", ""))
                parts.append(text_part)
        
        # Create Message object
        message = Message(
            messageId=message_data.get("messageId", "unknown"),
            role=Role.user,  # Default to user role
            parts=parts
        )
        
        # Create MessageSendParams
        send_params = MessageSendParams(message=message)
        
        # Create SendMessageRequest
        request = SendMessageRequest(
            id=jsonrpc_request.get("id"),
            params=send_params
        )
        
        return request
    
    async def call_agent(self, agent_url: str, jsonrpc_request: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """
        Call another agent using SLIM transport through central server.
        
        Args:
            agent_url: Target agent URL (e.g., "slim://legal-counsel")
            jsonrpc_request: JSON-RPC request payload
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing the agent's response
            
        Raises:
            Exception: If the call fails or times out
        """
        try:
            # Get central SLIM server endpoint (lungo pattern)
            import os
            slim_endpoint = os.getenv('SLIM_ENDPOINT', 'slim://slim:46357')
            
            # Convert slim:// agent URL to HTTP for agent discovery
            if agent_url.startswith('slim://'):
                # Extract agent name and convert to HTTP endpoint
                agent_name = agent_url.replace('slim://', '')
                # Map to HTTP endpoint for agent discovery
                http_agent_url = f"http://{agent_name}:9002"  # Default port, should be mapped per agent
                if 'sentiment-analyst' in agent_name:
                    http_agent_url = f"http://{agent_name}:9002"
                elif 'fact-checker' in agent_name:
                    http_agent_url = f"http://{agent_name}:9004"
                elif 'risk-score' in agent_name:
                    http_agent_url = f"http://{agent_name}:9003"
                elif 'legal-counsel' in agent_name:
                    http_agent_url = f"http://{agent_name}:9005"
                elif 'press-secretary' in agent_name:
                    http_agent_url = f"http://{agent_name}:9006"
                elif 'ear-to-ground' in agent_name:
                    http_agent_url = f"http://{agent_name}:9001"
            else:
                http_agent_url = agent_url
            
            # Create client if not cached (all go through central server)
            cache_key = f"{slim_endpoint}:{http_agent_url}"
            if cache_key not in self._clients:
                transport = self.factory.create_transport("SLIM", endpoint=slim_endpoint)
                client = await self.factory.create_client("A2A", agent_url=http_agent_url, transport=transport)
                self._clients[cache_key] = client
                logger.debug(f"Created new SLIM client for {http_agent_url} via {slim_endpoint}")
            
            client = self._clients[cache_key]
            
            # Convert JSON-RPC to A2A format
            a2a_request = self._convert_jsonrpc_to_a2a(jsonrpc_request)
            
            # Make the call with timeout
            logger.debug(f"Calling {agent_url} via central SLIM server with request: {jsonrpc_request}")
            result = await asyncio.wait_for(
                client.send_message(a2a_request),
                timeout=timeout
            )
            
            logger.debug(f"Response from {agent_url}: {result}")
            
            # Convert A2A response back to JSON-RPC format
            if hasattr(result, 'root') and result.root and hasattr(result.root, 'result'):
                # Extract the response message from the nested structure
                response_message = result.root.result
                
                # Start with basic message structure
                response_data = {
                    "id": jsonrpc_request.get("id"),
                    "jsonrpc": "2.0",
                    "result": {
                        "kind": response_message.kind,
                        "messageId": response_message.messageId,
                        "role": response_message.role.value,
                        "metadata": response_message.metadata or {},
                        "parts": [
                            {
                                "kind": part.root.kind if hasattr(part, 'root') else part.kind,
                                "text": part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else getattr(part, 'text', str(part))
                            }
                            for part in response_message.parts
                        ]
                    }
                }
                
                # Extract structured agent data from metadata and merge into result
                if response_message.metadata:
                    metadata = response_message.metadata
                    # Promote structured agent data to top level for extraction compatibility
                    for key, value in metadata.items():
                        if key not in ['name'] and isinstance(value, dict):
                            response_data["result"].update(value)
                
                return response_data
            else:
                # Handle error case
                return {
                    "id": jsonrpc_request.get("id"),
                    "jsonrpc": "2.0", 
                    "error": {"code": -1, "message": f"No result in response. Response: {result}"}
                }
            
        except asyncio.TimeoutError:
            logger.error(f"SLIM call to {agent_url} timed out after {timeout}s")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling {agent_url} via SLIM: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close all cached clients."""
        for agent_url, client in self._clients.items():
            try:
                if hasattr(client, 'close'):
                    await client.close()
            except Exception as e:
                logger.warning(f"Error closing client for {agent_url}: {e}")
        self._clients.clear()


# Global client instance for reuse
_slim_client = None

def get_slim_client() -> SlimClient:
    """Get the global SLIM client instance."""
    global _slim_client
    if _slim_client is None:
        _slim_client = SlimClient()
    return _slim_client


async def call_agent_slim(agent_url: str, jsonrpc_request: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
    """
    Convenience function for making SLIM calls.
    
    Args:
        agent_url: Target agent URL (e.g., "slim://legal-counsel:50055")
        jsonrpc_request: JSON-RPC request payload
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing the agent's response
    """
    client = get_slim_client()
    return await client.call_agent(agent_url, jsonrpc_request, timeout) 