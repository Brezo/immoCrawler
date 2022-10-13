class CrawlerConfig:
    def __init__(self, providers: [str] = [], notification_channel: str = '', database: str = '', db_user: str = '',
                 db_host: str = '', db_password: str = '', smtp_host: str = '', smtp_port: int = 0,
                 smtp_address: str = '', smtp_pwd: str = '',
                 recipients: [str] = [], subject: str = '', chat_id: str = '', bot_token: str = '',
                 surface_min=0, surface_max=0, postcode_filter: str = ''):
        self.providers = providers
        if notification_channel not in ('Mail', 'Telegram'):
            raise ValueError('Invalid notification channel')
        self.notification_channel = notification_channel
        self.database = database
        self.db_user = db_user
        self.db_host = db_host
        self.db_password = db_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_address = smtp_address
        self.smtp_pwd = smtp_pwd
        self.recipients = recipients
        self.subject = subject
        self.chat_id = chat_id
        self.bot_token = bot_token
        self.surface_min = surface_min
        self.surface_max = surface_max
        self.postcode_filter = postcode_filter
