import logging

from brief import build_brief, render_brief_html
from services.telegram import send_message

logger = logging.getLogger(__name__)

def run_brief():
    logger.info("run_brief started")
    brief = build_brief()
    logger.info("brief built successfully")
    message = render_brief_html(brief)
    logger.info("brief rendered successfully")
    send_message(message)
    logger.info("telegram message sent successfully")

def main():
    run_brief()

if __name__ == "__main__":
    main()