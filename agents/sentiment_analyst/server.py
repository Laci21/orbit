"""Server for the Sentiment Analyst agent."""

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

from agents.sentiment_analyst.agent_executor import SentimentAnalystAgentExecutor
from agents.sentiment_analyst.card import AGENT_CARD
from agents.sentiment_analyst.config import SentimentAnalystConfig

load_dotenv()

logger = logging.getLogger("orbit.sentiment_analyst_agent.server")


class SentimentAnalystServer:
    """Server for the Sentiment Analyst agent."""
    
    def __init__(self, config: Optional[SentimentAnalystConfig] = None):
        self.config = config or SentimentAnalystConfig()
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
        """Start the Sentiment Analyst agent server."""
        logger.info(f"Starting Sentiment Analyst agent on port {self.config.agent_port}")
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Create A2A application  
        request_handler = DefaultRequestHandler(
            agent_executor=SentimentAnalystAgentExecutor(),
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(
            agent_card=AGENT_CARD,
            http_handler=request_handler
        )
        
        # Create uvicorn server
        config = Config(
            app=self.app.build(),
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
            logger.info("Sentiment Analyst agent server stopped")
            
    async def stop(self) -> None:
        """Stop the Sentiment Analyst agent server."""
        self._shutdown_event.set()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = SentimentAnalystServer()
    asyncio.run(server.start())