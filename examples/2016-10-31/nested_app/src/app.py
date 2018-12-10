import logging

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def process_tweets(tweets, context):
    LOGGER.info("Received tweets: {}".format(tweets))
