"""Server for the Ear-to-Ground agent."""

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

from agents.ear_to_ground.agent_executor import EarToGroundAgentExecutor
from agents.ear_to_ground.card import AGENT_CARD
from agents.ear_to_ground.config import EarToGroundConfig
from agents.ear_to_ground.streaming_service import TweetStreamingService

load_dotenv()

logger = logging.getLogger(__name__)


class EarToGroundServer:
    """Server for the Ear-to-Ground agent."""
    
    def __init__(self, config: Optional[EarToGroundConfig] = None):
        self.config = config or EarToGroundConfig()
        self.app = None
        self.streaming_service = None
        self._shutdown_event = asyncio.Event()
        
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, _):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self._shutdown_event.set()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def start(self) -> None:
        """Start the Ear-to-Ground agent server."""
        logger.info(f"Starting Ear-to-Ground agent on port {self.config.agent_port}")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create A2A application  
        request_handler = DefaultRequestHandler(
            agent_executor=EarToGroundAgentExecutor(),
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(
            agent_card=AGENT_CARD,
            http_handler=request_handler
        )
        
        # Start HTTP server for direct A2A calls
        config = Config(
            app=self.app.build(), 
            host="0.0.0.0", 
            port=self.config.agent_port, 
            loop="asyncio"
        )
        userver = Server(config)
        
        # Create streaming service
        self.streaming_service = TweetStreamingService(None, None)
        
        # Run HTTP server and streaming service concurrently
        tasks = [
            asyncio.create_task(userver.serve()),
            asyncio.create_task(self.streaming_service.start())
        ]
        
        logger.info(f"HTTP A2A server started on port {self.config.agent_port}")
        logger.info("Tweet streaming service starting...")
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down Ear-to-Ground agent server")
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
        
        if self.streaming_service:
            self.streaming_service.stop()
            
        # Give streaming service time to finish current operations
        await asyncio.sleep(2)
        
        logger.info("Cleanup completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = EarToGroundServer()
    asyncio.run(server.start())