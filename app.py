import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import HOST, PORT, DATABASE_PATH
from src.core.logging_config import setup_logging
from src.database.db import init_database
from src.api.routes import router, serve_frontend

setup_logging()
logger = logging.getLogger(__name__)

init_database(DATABASE_PATH)

app = FastAPI(
    title="SmartResolve",
    description="Telecom Operations Resolution Assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
serve_frontend(app)

if __name__ == "__main__":
    logger.info("Starting SmartResolve on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT)
