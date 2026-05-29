"""
main.py
-------
Entry point for the Intervue AI Pipecat agent service.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from utils.logger import setup_logging
from server.startup import make_lifespan
from server.routes import health, start_simulation, end_simulation
from server.token_route import participant_token

setup_logging(config.env)

app = FastAPI(title="Intervue Agent Service", version="1.0.0", lifespan=make_lifespan())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.get("/health")(health)
app.post("/start")(start_simulation)
app.post("/end")(end_simulation)
app.get("/participant-token")(participant_token)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.is_dev,
    )