"""Server for the Press Secretary agent."""

import asyncio
import logging
import signal
import sys
from typing import Optional
from uvicorn import Config, Server

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

from agents.press_secretary.agent_executor import PressSecretaryAgentExecutor
from agents.press_secretary.card import AGENT_CARD
from agents.press_secretary.config import PressSecretaryConfig

load_dotenv()

logger = logging.getLogger("orbit.press_secretary_agent.server")


class PressSecretaryServer:
    """Server for the Press Secretary agent."""
    
    def __init__(self, config: Optional[PressSecretaryConfig] = None):
        self.config = config or PressSecretaryConfig()
        self.app = None
        self._shutdown_event = asyncio.Event()
        
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, _):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def start(self) -> None:
        """Start the Press Secretary agent server."""
        logger.info(f"Starting Press Secretary agent on port {self.config.agent_port}")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create A2A application  
        request_handler = DefaultRequestHandler(
            agent_executor=PressSecretaryAgentExecutor(),
            agent_card=AGENT_CARD,
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(request_handler=request_handler)
        
        # Create uvicorn server
        config = Config(
            app=self.app,
            host="0.0.0.0",
            port=self.config.agent_port,
            log_level="info"
        )
        
        server = Server(config)
        
        # Run server until shutdown signal
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            logger.info("Press Secretary agent server stopped")
    
    async def stop(self) -> None:
        """Stop the Press Secretary agent server."""
        self._shutdown_event.set()


# Main execution
if __name__ == "__main__":
    server = PressSecretaryServer()
    asyncio.run(server.start()) 