# SLIM Integration Implementation Plan
## Based on coffeeAgntcy/lungo Pattern

## 1. Overview

This document outlines the implementation of SLIM (Secure Low-latency Interactive Messaging) integration for Orbit, following the architecture pattern from the [coffeeAgntcy lungo example](https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/lungo).

### Key Architectural Decisions:
- **Central SLIM Server**: Single SLIM server that all agents connect to (lungo pattern)
- **Request-Reply Communication**: All inter-agent calls use request-reply pattern
- **Port**: SLIM server runs on port 46357 (matching lungo)
- **Transport**: All agents use SLIM transport through GatewayFactory
- **Service Discovery**: Agents use agent names without specific ports (e.g., `slim://sentiment-analyst`)

## 2. Dependencies

Added to `requirements.txt`:
```
agntcy-app-sdk>=0.2.0
slim-bindings>=0.1.0
grpcio>=1.60
```

## 3. SLIM Server Configuration

### Docker Compose Service:
```yaml
slim:
  image: ghcr.io/agntcy/slim:0.3.15
  container_name: slim
  ports:
    - "46357:46357"
  environment:
    - PASSWORD=${SLIM_GATEWAY_PASSWORD:-dummy_password}
    - CONFIG_PATH=/config.yaml
  volumes:
    - ./config/docker/slim/server-config.yaml:/config.yaml
  command: ["/slim", "--config", "/config.yaml"]
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:46357/health"]
    interval: 10s
    timeout: 5s
    retries: 3
  restart: unless-stopped
```

### SLIM Configuration (`config/docker/slim/server-config.yaml`):
```yaml
tracing:
  log_level: info
  display_thread_names: true
  display_thread_ids: true

runtime:
  n_cores: 0
  thread_name: "slim-data-plane"
  drain_timeout: 10s

services:
  slim/0:
    pubsub:
      servers:
        - endpoint: "0.0.0.0:46357"
          tls:
            insecure: true
      clients: []
    controller:
      server:
        endpoint: "0.0.0.0:46358"
        tls:
          insecure: true
```

## 4. Agent Configuration

### Environment Variables (SLIM-only):
All **internal** HTTP endpoints/ports have been removed.  Agents now expose only their SLIM address; HTTP is kept *solely* for the Gateway → Ear-to-Ground UI (port 9001).

Each agent gets:
```yaml
environment:
  - SLIM_ENDPOINT=slim://slim:46357
  - OTHER_AGENT_URL=slim://agent-name  # No port needed
```

### Example for ear-to-ground:
```yaml
environment:
  - SLIM_ENDPOINT=slim://slim:46357
  - SENTIMENT_ANALYST_URL=slim://sentiment-analyst
  - FACT_CHECKER_URL=slim://fact-checker
  - RISK_SCORE_URL=slim://risk-score
  - PRESS_SECRETARY_URL=slim://press-secretary
```

## 5. Server-side Implementation

Each agent server connects to the central SLIM server:

```python
from agntcy_app_sdk.factory import GatewayFactory, TransportTypes

# In server.py start() method:
factory = GatewayFactory()
slim_endpoint = os.getenv('SLIM_ENDPOINT', 'slim://slim:46357')
slim_transport = factory.create_transport(
    transport=TransportTypes.SLIM.value,
    endpoint=slim_endpoint
)

self.bridge = factory.create_bridge(self.app, transport=slim_transport)
await self.bridge.start()
```

## 6. Client-side Implementation

### SLIM Client Helper (`common/slim_client.py`):
```python
from agntcy_app_sdk.factory import GatewayFactory

class SlimClient:
    def __init__(self):
        self.factory = GatewayFactory()
        self._clients = {}

    async def call_agent(self, agent_url: str, jsonrpc_request: dict, timeout: float = 30.0):
        # All calls go through central SLIM server
        slim_endpoint = os.getenv('SLIM_ENDPOINT', 'slim://slim:46357')
        
        if slim_endpoint not in self._clients:
            transport = self.factory.create_transport("SLIM", endpoint=slim_endpoint)
            client = await self.factory.create_client("A2A", agent_url=agent_url, transport=transport)
            self._clients[slim_endpoint] = client
        
        client = self._clients[slim_endpoint]
        return await client.request(jsonrpc_request)
```

### Usage in Agent Executors:
```python
from common.slim_client import call_agent_slim

# Replace aiohttp calls:
result = await call_agent_slim(
    self.config.legal_counsel_endpoint,  # slim://legal-counsel
    request_payload,
    timeout=30.0
)
```

## 7. Testing

### Basic SLIM Server Test:
```bash
# Check if SLIM server is running
curl http://localhost:46357/health

# Test gRPC endpoints
grpcurl -plaintext localhost:46357 list
```

### Integration Test (manual)
Trigger a crisis through the Gateway (or directly via Ear-to-Ground) and verify all agents report `SLIM gRPC bridge connected` and the final crisis response is generated without errors.

## 8. Migration Status

✅ **Completed:**
- Docker compose SLIM server setup
- SLIM server configuration
- All agent server.py files updated
- All agent environment variables updated
- SLIM client helper implementation
- Agent executor updates
- Manual integration test verified (crisis trigger)

## 9. Benefits

- **Performance**: gRPC-based communication vs HTTP
- **Central Management**: Single SLIM server for all communication
- **Service Discovery**: Simplified agent addressing
- **Request-Reply**: Familiar communication pattern
- **Reliability**: Built-in error handling and timeouts

## 10. Next Steps

1. Test the implementation: `docker compose build && docker compose up -d`
2. Verify SLIM server health: `curl http://localhost:46357/health`
3. Monitor agent logs for successful SLIM connections and ensure each agent prints `SLIM gRPC bridge connected`.

This implementation follows the lungo pattern exactly, ensuring compatibility and leveraging proven architecture patterns.
