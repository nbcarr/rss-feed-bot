import logging

from constants import FEEDS_FILE, STATE_FILE
from objects.twitterbot import TwitterBot
from utils import parse_args

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    args = parse_args()
    logger.info(f"Running with arguments: {args}")
    bot = TwitterBot(STATE_FILE, FEEDS_FILE, logger, dryrun=args.dryrun)
    bot.run()


if __name__ == "__main__":
    main()
