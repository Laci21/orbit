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
        self.agent_progress: Dict[str, str] = {}  # Track which agents are working

# Global crisis state
crisis_state = CrisisState()

# Response models
class CrisisStatusResponse(BaseModel):
    crisis_id: Optional[str]
    status: str
    started_at: Optional[datetime]
    final_response: Optional[Dict[str, Any]]
    last_update: Optional[datetime]
    agent_progress: Dict[str, str] = {}  # Which agents are currently working

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
        last_update=crisis_state.last_update,
        agent_progress=crisis_state.agent_progress
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
    """Monitor crisis progress with simple polling every 3 seconds."""
    try:
        logger.info("Starting crisis monitoring with 3-second polling...")
        
        # Simple polling every 3 seconds
        for i in range(30):  # Check every 3 seconds for 90 seconds total
            await asyncio.sleep(3)
            logger.info(f"Crisis monitoring check {i+1}/30...")
            
            # Try to get final results from Ear-to-Ground
            final_result = await get_crisis_results_from_ear_to_ground()
            
            if final_result and not final_result.get("error"):
                # Update last update time
                crisis_state.last_update = datetime.now()
                
                # Check if we found the Press Secretary response
                if final_result.get("press_secretary_response"):
                    crisis_state.final_response = final_result
                    crisis_state.status = "complete"
                    logger.info("✅ Crisis complete - Press Secretary response received!")
                    return
                else:
                    logger.info(f"Got response but no Press Secretary data yet (check {i+1}/30)")
            else:
                logger.info(f"No response from Ear-to-Ground yet (check {i+1}/30)")
         
        # Timeout - mark as complete anyway
        logger.warning("Crisis monitoring timeout after 90s - marking as complete")
        crisis_state.status = "complete"
        crisis_state.last_update = datetime.now()
         
    except Exception as e:
        logger.error(f"Error monitoring crisis progress: {e}")
        crisis_state.status = "error"
        crisis_state.last_update = datetime.now()

async def get_crisis_results_from_ear_to_ground() -> Optional[Dict[str, Any]]:
    """Get final crisis results from Ear-to-Ground orchestration."""
    try:
        # Query Ear-to-Ground for status/results including final crisis response
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
                            "text": "Provide status and final results"  # This will trigger final response inclusion
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
                
                # Try to extract the final crisis response from Ear-to-Ground metadata
                final_crisis_response = None
                if isinstance(result, dict) and "result" in result:
                    result_data = result["result"]
                    if isinstance(result_data, dict) and "metadata" in result_data:
                        metadata = result_data["metadata"]
                        if isinstance(metadata, dict) and "final_crisis_response" in metadata:
                            final_crisis_response = metadata["final_crisis_response"]
                            logger.info("Extracted final crisis response from Ear-to-Ground")
                 
                # Only proceed with extraction if we actually have final crisis response data
                # If we have a final crisis response, extract the Press Secretary data
                if final_crisis_response:
                    press_secretary_data = extract_press_secretary_response(final_crisis_response)
                    if press_secretary_data:
                        logger.info("✅ Crisis response complete - Press Secretary data ready")
                        return {"press_secretary_response": press_secretary_data}
                    else:
                        logger.warning("Press Secretary data not found in final response")
                else:
                    # No final crisis response in metadata yet
                    pass  # Normal during polling - no need to log
                
                # Don't return the result if it doesn't have Press Secretary data
                # This will make the polling continue
                return None
            else:
                logger.error(f"Failed to get results from Ear-to-Ground: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error getting crisis results: {e}")
        return None

def extract_press_secretary_response(final_crisis_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract Press Secretary response data from the final crisis response."""
    try:
        # The final_crisis_response should be the JSON-RPC response from Press Secretary
        if isinstance(final_crisis_response, dict) and "result" in final_crisis_response:
            result = final_crisis_response["result"]
            
            if isinstance(result, dict) and "metadata" in result:
                metadata = result["metadata"]
                
                if isinstance(metadata, dict) and "press_response" in metadata:
                    return metadata["press_response"]
                else:
                    logger.warning("❌ No press_response key in metadata")
            else:
                logger.warning("❌ No metadata in result or result is not dict")
        else:
            logger.warning("❌ No result key in final_crisis_response or not dict")
        
        return None
    except Exception as e:
        logger.error(f"Error extracting Press Secretary response: {e}")
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