"""
FastAPI server for Kernel Universe simulation.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import redis

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config
from .simulation import KernelUniverseSimulation


# Initialize Redis connection
redis_client = redis.Redis.from_url(config.REDIS_URL)

# Initialize simulation
simulation = KernelUniverseSimulation()

# Initialize FastAPI app
app = FastAPI(
    title="Kernel Universe API",
    description="API for controlling and monitoring the Kernel Universe simulation",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: List[WebSocket] = []

# Simulation state
paused = False
step_interval = 1.0 / 10  # 10 steps per second
stream_interval = 1.0 / config.STREAM_FPS


class SimulationControl(BaseModel):
    """Model for simulation control parameters."""
    paused: Optional[bool] = None
    reset: Optional[bool] = None
    step_rate: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None


async def broadcast_state():
    """Broadcast simulation state to all connected clients."""
    if not active_connections:
        return
    
    state = simulation.get_state()
    
    # Convert numpy arrays to lists for JSON serialization
    state_json = json.dumps({
        "tick": state["tick"],
        "temperature": state["temperature"],
        "catalyst_upper": state["catalyst_upper"],
        "catalyst_lower": state["catalyst_lower"],
        "cores": state["cores"],
        "total_blooms": state["total_blooms"],
        "runtime": state["runtime"]
    })
    
    # Store in Redis
    redis_client.set(config.REDIS_STATE_KEY, state_json)
    
    # Broadcast to all WebSocket connections
    for connection in active_connections:
        await connection.send_text(state_json)


async def simulation_loop():
    """Main simulation loop that runs in the background."""
    last_step_time = time.time()
    last_stream_time = time.time()
    
    while True:
        current_time = time.time()
        
        # Step simulation if not paused
        if not paused and (current_time - last_step_time) >= step_interval:
            simulation.step()
            last_step_time = current_time
        
        # Stream updates at the configured FPS
        if (current_time - last_stream_time) >= stream_interval:
            await broadcast_state()
            last_stream_time = current_time
        
        # Yield to allow other tasks to run
        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup_event():
    """Start the simulation loop when the server starts."""
    asyncio.create_task(simulation_loop())


@app.get("/snapshot")
async def get_snapshot():
    """Get the current simulation state."""
    # Try to get from Redis first
    cached_state = redis_client.get(config.REDIS_STATE_KEY)
    if cached_state:
        return json.loads(cached_state)
    
    # Otherwise get directly from simulation
    return simulation.get_state()


@app.post("/control")
async def control_simulation(control: SimulationControl):
    """Control the simulation."""
    global paused, step_interval
    
    # Update pause state if specified
    if control.paused is not None:
        paused = control.paused
    
    # Reset simulation if requested
    if control.reset:
        simulation.reset()
    
    # Update step rate if specified
    if control.step_rate is not None and control.step_rate > 0:
        step_interval = 1.0 / control.step_rate
    
    # Update parameters if specified
    if control.parameters:
        for param_name, value in control.parameters.items():
            success = simulation.set_parameter(param_name, value)
            if not success:
                raise HTTPException(status_code=400, detail=f"Unknown parameter: {param_name}")
    
    return {
        "paused": paused,
        "step_rate": 1.0 / step_interval,
        "parameters": {
            "GRID_SIZE": config.GRID_SIZE,
            "C_THRESH": config.C_THRESH,
            "EMIT_FRACTION": config.EMIT_FRACTION,
            "ADVECT_ALPHA": config.ADVECT_ALPHA,
            "T_MIN": config.T_MIN,
            "T_MAX": config.T_MAX,
            "TAU_TEMP": config.TAU_TEMP,
            "TAU_CATALYST": config.TAU_CATALYST,
            "TAU_REFRACT": config.TAU_REFRACT,
            "SPAWN_S": config.SPAWN_S
        }
    }


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming simulation updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial state
        state = simulation.get_state()
        await websocket.send_json(state)
        
        # Keep connection open and handle commands
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                if "control" in command:
                    control = SimulationControl(**command["control"])
                    await control_simulation(control)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"error": str(e)})
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("kernel_universe.server:app", host=config.API_HOST, port=config.API_PORT, reload=True)