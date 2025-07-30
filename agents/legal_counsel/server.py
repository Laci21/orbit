"""Server for the Legal Counsel agent."""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional
from uvicorn import Config, Server

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

# SLIM integration imports
from agntcy_app_sdk.factory import GatewayFactory, TransportTypes

from agents.legal_counsel.agent_executor import LegalCounselAgentExecutor
from agents.legal_counsel.card import AGENT_CARD
from agents.legal_counsel.config import LegalCounselConfig

load_dotenv()

logger = logging.getLogger("orbit.legal_counsel_agent.server")


class LegalCounselServer:
    """Server for the Legal Counsel agent."""
    
    def __init__(self, config: Optional[LegalCounselConfig] = None):
        self.config = config or LegalCounselConfig()
        self.app = None
        self.bridge = None
        self._shutdown_event = asyncio.Event()
        
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, _):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def start(self) -> None:
        """Start the Legal Counsel agent server."""
        logger.info(f"Starting Legal Counsel agent on port {self.config.agent_port}")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create A2A application  
        request_handler = DefaultRequestHandler(
            agent_executor=LegalCounselAgentExecutor(),
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(
            agent_card=AGENT_CARD,
            http_handler=request_handler
        )
        
        # Setup SLIM bridge to central server
        factory = GatewayFactory()
        slim_endpoint = os.getenv('SLIM_ENDPOINT', 'slim://slim:46357')
        slim_transport = factory.create_transport(
            transport=TransportTypes.SLIM.value,
            endpoint=slim_endpoint
        )
        
        self.bridge = factory.create_bridge(self.app, transport=slim_transport)
        
        # Start SLIM bridge (connects to central server)
        logger.info(f"Connecting to central SLIM server at {slim_endpoint}")
        await self.bridge.start()
        
        # Start HTTP server for UI compatibility
        config = Config(
            app=self.app.build(), 
            host="0.0.0.0", 
            port=self.config.agent_port, 
            loop="asyncio"
        )
        userver = Server(config)
        logger.info(f"HTTP A2A server started on port {self.config.agent_port}")
        logger.info(f"SLIM gRPC bridge connected to {slim_endpoint}")
        
        # Run HTTP server
        try:
            await userver.serve()
        except KeyboardInterrupt:
            logger.info("Shutting down Legal Counsel agent server")
        except Exception as e:
            logger.error(f"Error running server: {e}")
            raise
            
    async def _wait_for_shutdown(self) -> None:
        """Wait for shutdown event."""
        await self._shutdown_event.wait()
        logger.info("Shutdown event received")
        
    async def _cleanup(self) -> None:
        """Cleanup resources during shutdown."""
        logger.info("Starting cleanup...")
        if self.bridge:
            # Bridge cleanup would be handled by the factory if needed
            pass
        logger.info("Cleanup completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = LegalCounselServer()
    asyncio.run(server.start()) 