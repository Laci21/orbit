"""Minimal FastAPI Gateway for Orbit Crisis Management System."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orbit.gateway")

app = FastAPI(title="Orbit Crisis Management Gateway", version="1.0.0")

# Enable CORS for React frontend (both dev and prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],  # Vite dev server + FastAPI
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ear-to-Ground agent endpoint (acts as orchestrator)
EAR_TO_GROUND_ENDPOINT = os.getenv("EAR_TO_GROUND_URL", "http://localhost:9001")

# In-memory crisis state
class CrisisState:
    def __init__(self):
        self.crisis_id: Optional[str] = None
        self.status: str = "idle"  # idle, active, complete, error
        self.started_at: Optional[datetime] = None
        self.final_response: Optional[Dict[str, Any]] = None
        self.last_update: Optional[datetime] = None

# Global crisis state
crisis_state = CrisisState()

# Response models
class CrisisStatusResponse(BaseModel):
    crisis_id: Optional[str]
    status: str
    started_at: Optional[datetime]
    final_response: Optional[Dict[str, Any]]
    last_update: Optional[datetime]

class TriggerRequest(BaseModel):
    tweet_content: Optional[str] = "BREAKING: Major allegations surface against company executive. Investigation needed immediately. #CrisisAlert"

@app.get("/api/crisis/status", response_model=CrisisStatusResponse)
async def get_crisis_status():
    """Get current crisis status from Ear-to-Ground orchestration."""
    return CrisisStatusResponse(
        crisis_id=crisis_state.crisis_id,
        status=crisis_state.status,
        started_at=crisis_state.started_at,
        final_response=crisis_state.final_response,
        last_update=crisis_state.last_update
    )

@app.post("/api/crisis/trigger")
async def trigger_crisis(request: TriggerRequest):
    """Trigger crisis by calling Ear-to-Ground agent directly."""
    try:
        # Reset crisis state
        crisis_state.crisis_id = f"crisis_{int(datetime.now().timestamp())}"
        crisis_state.status = "active"
        crisis_state.started_at = datetime.now()
        crisis_state.final_response = None
        crisis_state.last_update = datetime.now()
        
        logger.info(f"Triggering crisis via Ear-to-Ground: {crisis_state.crisis_id}")
        
        # Call Ear-to-Ground agent directly to start orchestration
        result = await call_ear_to_ground_agent(request.tweet_content)
        
        if result and not result.get("error"):
            logger.info("Crisis successfully triggered via Ear-to-Ground")
            # Start monitoring task to track progress
            asyncio.create_task(monitor_crisis_progress())
        else:
            logger.error(f"Failed to trigger crisis: {result}")
            crisis_state.status = "error"
        
        return {
            "success": True,
            "crisis_id": crisis_state.crisis_id,
            "message": "Crisis triggered via Ear-to-Ground orchestrator"
        }
        
    except Exception as e:
        logger.error(f"Error triggering crisis: {e}")
        crisis_state.status = "error"
        raise HTTPException(status_code=500, detail=str(e))

async def call_ear_to_ground_agent(tweet_content: str) -> Optional[Dict[str, Any]]:
    """Call Ear-to-Ground agent to start crisis orchestration."""
    try:
        # Prepare A2A JSON-RPC request to trigger crisis workflow
        request_payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"trigger-{crisis_state.crisis_id}",
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": f"Start streaming crisis tweets with content: {tweet_content}"
                        }
                    ]
                }
            },
            "id": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{EAR_TO_GROUND_ENDPOINT}/",
                json=request_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Ear-to-Ground agent called successfully")
                return result
            else:
                error_text = await response.aread()
                logger.error(f"Ear-to-Ground call failed: {response.status_code} - {error_text}")
                return {"error": f"HTTP {response.status_code}: {error_text}"}
                
    except httpx.TimeoutException:
        logger.error("Ear-to-Ground agent call timed out")
        return {"error": "Request timed out"}
    except Exception as e:
        logger.error(f"Error calling Ear-to-Ground agent: {e}")
        return {"error": str(e)}

async def monitor_crisis_progress():
    """Monitor crisis progress by checking Ear-to-Ground status."""
    try:
        # Simple monitoring - wait for crisis completion
        # In a real implementation, this would poll Ear-to-Ground for status updates
        
        # Give the workflow time to complete
        for i in range(6):  # Check every 10 seconds for 1 minute
            await asyncio.sleep(10)
            logger.info(f"Crisis monitoring check {i+1}/6...")
            
            # Try to get status/results from Ear-to-Ground
            final_result = await get_crisis_results_from_ear_to_ground()
            if final_result and not final_result.get("error"):
                crisis_state.final_response = final_result
                crisis_state.status = "complete"
                logger.info("Crisis orchestration completed successfully")
                crisis_state.last_update = datetime.now()
                return
        
        # If we get here, the workflow didn't complete in time
        logger.warning("Crisis monitoring timeout - no final results received after 60s")
        crisis_state.status = "complete"  # Assume it completed, just didn't get results
        crisis_state.last_update = datetime.now()
        
    except Exception as e:
        logger.error(f"Error monitoring crisis progress: {e}")
        crisis_state.status = "error"
        crisis_state.last_update = datetime.now()

async def get_crisis_results_from_ear_to_ground() -> Optional[Dict[str, Any]]:
    """Get final crisis results from Ear-to-Ground orchestration."""
    try:
        # Query Ear-to-Ground for status/results
        request_payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": f"status-{crisis_state.crisis_id}",
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": "Provide status and final results"
                        }
                    ]
                }
            },
            "id": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{EAR_TO_GROUND_ENDPOINT}/",
                json=request_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Retrieved crisis results from Ear-to-Ground")
                return result
            else:
                logger.error(f"Failed to get results from Ear-to-Ground: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting crisis results: {e}")
        return None

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Serve React frontend static files
frontend_build_path = Path(__file__).parent / "frontend" / "dist"
if frontend_build_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_build_path), html=True), name="frontend")
    logger.info(f"Serving React frontend from {frontend_build_path}")
else:
    logger.warning(f"Frontend build directory not found: {frontend_build_path}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GATEWAY_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)