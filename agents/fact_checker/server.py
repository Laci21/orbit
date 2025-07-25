"""Server for the Fact Checker agent."""

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

from agents.fact_checker.agent_executor import FactCheckerAgentExecutor
from agents.fact_checker.card import AGENT_CARD
from agents.fact_checker.config import FactCheckerConfig

load_dotenv()

logger = logging.getLogger("orbit.fact_checker_agent.server")


class FactCheckerServer:
    """Server for the Fact Checker agent."""
    
    def __init__(self, config: Optional[FactCheckerConfig] = None):
        self.config = config or FactCheckerConfig()
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
        """Start the Fact Checker agent server."""
        logger.info(f"Starting Fact Checker agent on port {self.config.agent_port}")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create A2A application  
        request_handler = DefaultRequestHandler(
            agent_executor=FactCheckerAgentExecutor(),
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(
            agent_card=AGENT_CARD,
            http_handler=request_handler
        )
        
        # No SLIM transport needed - using direct A2A calls only
        
        # Start HTTP server for direct A2A calls only (no SLIM)
        config = Config(
            app=self.app.build(), 
            host="0.0.0.0", 
            port=self.config.agent_port, 
            loop="asyncio"
        )
        userver = Server(config)
        logger.info(f"HTTP A2A server started on port {self.config.agent_port}")
        
        # Run only the HTTP server (no SLIM bridges needed)
        try:
            await userver.serve()
        except KeyboardInterrupt:
            logger.info("Shutting down Fact Checker agent server")
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
        logger.info("Cleanup completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = FactCheckerServer()
    asyncio.run(server.start()) 