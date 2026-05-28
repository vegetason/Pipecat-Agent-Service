"""
main.py
-------
Entry point for the Intervue AI Pipecat agent service.
Node.js calls POST /start to boot a simulation.

In development, POST /start loads from dev_fixtures/simulation_context.json.
"""

import uvicorn
from fastapi import FastAPI

from config import config
from utils.logger import setup_logging
from server.startup import make_lifespan
from server.routes import health, start_simulation, end_simulation

setup_logging(config.env)

app = FastAPI(title="Intervue Agent Service", version="1.0.0", lifespan=make_lifespan())

app.get("/health")(health)
app.post("/start")(start_simulation)
app.post("/end")(end_simulation)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.is_dev,
    )
