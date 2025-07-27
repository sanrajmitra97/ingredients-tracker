from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import logging

from src.asqlite_class import SqliteManager

# Constants
DB_NAME = os.environ["DB_NAME"]
asqlite_manager = None

# Set up logger
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global asqlite_manager
    asqlite_manager = SqliteManager(db_name=DB_NAME)
    await asqlite_manager.connect()
    yield
    await asqlite_manager.close()

app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)