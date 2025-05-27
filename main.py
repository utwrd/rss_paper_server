import uvicorn
import asyncio
import logging
from web_app import app
from config import settings
from database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application"""
    logger.info("Starting RSS Summarizer application...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables initialized")
    
    # Start the web application
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
