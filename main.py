from typing import Optional

import ImmoCrawler
import datetime
import pytz
import configparser
import sys
import getopt
import ProviderFetchers
from ImmoCrawler import CrawlerConfig


def arg_usage():
    arg_help = "{0} -c <path/config.ini>".format(sys.argv[0])
    print(arg_help)


def get_config(argv) -> Optional[CrawlerConfig]:
    providers = []
    notification_channel = ''
    database = ''
    db_user = ''
    db_host = ''
    db_password = ''
    smtp_host = ''
    smtp_address = ''
    smtp_pwd = ''
    smtp_port = 0
    recipients = []
    subject = ''
    chat_id = ''
    bot_token = ''
    surface_min = 0
    surface_max = 0
    postcode_filter = ''

    optlist, args = getopt.getopt(argv[1:], 'hc:')
    config_path = ''
    for opt, arg in optlist:
        if opt == '-c':
            config_path = arg
        elif opt == '-h':
            arg_usage()
            return None

    if config_path == '':
        print('Config parameter missing!')
        arg_usage()
        return None

    config_parser = configparser.RawConfigParser()
    config_parser.read(config_path)

    providers = config_parser.get("General", "providers").splitlines()
    notification_channel = config_parser.get("General", "notification_channel")
    database = config_parser.get("DB", "database")
    db_user = config_parser.get("DB", "db_user")
    db_host = config_parser.get("DB", "db_host")
    db_password = config_parser.get("DB", "db_password")
    if config_parser.has_option("General", "surface_min"):
        surface_min = config_parser.getint("General","surface_min")
    if config_parser.has_option("General", "surface_max"):
        surface_max = config_parser.getint("General","surface_max")
    if config_parser.has_option("General", "postcode_filter"):
        postcode_filter = config_parser.get("General", "postcode_filter")

    if notification_channel == 'Mail':
        smtp_host = config_parser.get("Mail", "smtp_host")
        smtp_port = config_parser.getint("Mail", "smtp_port")
        smtp_address = config_parser.get("Mail", "smtp_address")
        smtp_pwd = config_parser.get("Mail", "smtp_pwd")
        recipients = config_parser.get("Mail", "recipients").splitlines()
    if notification_channel == 'Telegram':
        chat_id = config_parser.get("Telegram", "chat_id")
        bot_token = config_parser.get("Telegram", "bot_token")

    crawler_config = ImmoCrawler.CrawlerConfig(providers, notification_channel, database, db_user, db_host,
                                               db_password, smtp_host, smtp_port, smtp_address, smtp_pwd,
                                               recipients, subject, chat_id, bot_token, surface_min, surface_max,
                                               postcode_filter)

    return crawler_config


try:
    config = get_config(sys.argv)
except getopt.GetoptError as err:
    print(err)
    sys.exit(2)
except configparser.Error as err:
    print(err)
    sys.exit(2)
except ValueError as err:
    print(err)
    sys.exit(2)

if config is None:
    print("Config Error")
    sys.exit(2)

print("Processing start: " + str(datetime.datetime.now(pytz.timezone("Europe/Vienna"))))

notification_service = ImmoCrawler.ImmoNotificationService(config)

for provider in config.providers:
    print("-----\nProcessing: " + provider)
    try:
        fetcher = ImmoCrawler.ImmoFetcher(provider, config)
        db_writer = ImmoCrawler.ImmoDbWriter(provider, config)
    except KeyError as error:
        print("Error: Provider " + provider + " not implemented!")
        continue

    crawled_immo = fetcher.fetch()
    print(str(len(crawled_immo)) + " entries fetched")
    db_writer.write_data(crawled_immo, notification_service)

notification_service.send_notification()
