from ImmoCrawler import CrawledImmo, CrawlerConfig
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests


class ImmoNotificationService:
    ignore_status = ["Reserviert", "removed"]

    def __init__(self, config: CrawlerConfig):
        self.new_immo = []
        self.changed_immo = []
        self.config: CrawlerConfig = config

    def add_immo(self, new_immo: [CrawledImmo], changed_immo: [CrawledImmo]) -> None:
        self.new_immo.extend(new_immo)
        self.changed_immo.extend([x for x in changed_immo if x.status not in ImmoNotificationService.ignore_status])

    def send_notification(self) -> None:
        # check if any data available for notification
        if (len(self.new_immo) == 0 and
                len(self.changed_immo) == 0):
            return

        insert_string = self.get_message_body("NEU", self.new_immo)
        update_string = self.get_message_body("ÄNDERUNGEN", self.changed_immo)

        if len(insert_string) == 0 and len(update_string) == 0:
            return

        if len(insert_string) > 0 and len(update_string) > 0:
            update_string = ("\n\n\n" + update_string)
        message = (insert_string + update_string)

        if self.config.notification_channel == "Mail":
            self.send_mail(message)
        elif self.config.notification_channel == "Telegram":
            self.send_telegram(message)

    def send_telegram(self, message) -> None:
        # obtaining chat-ids and bot tokens:
        # https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id
        # https://stackoverflow.com/a/67152755
        # split message into chunks to stay in telegram api limit
        chunk_size = 4000
        chunks = [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]
        for chunk in chunks:
            url = f"https://api.telegram.org/bot{self.config.bot_token}"
            params = {"chat_id": self.config.chat_id, "text": chunk}
            r = requests.get(url + "/sendMessage", params=params)
        print("Telegram OK")

    def send_mail(self, message) -> None:

        s = self.get_smtp()

        msg = MIMEMultipart()

        # set up the parameters of the message
        msg['From'] = self.config.smtp_address
        msg['To'] = ";".join(self.config.mail_recipients)
        msg['Subject'] = self.config.subject

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        s.send_message(msg)
        print("Mail OK")

    def get_smtp(self):
        s = smtplib.SMTP(host=self.config.smtp_host, port=self.config.smtp_port)
        s.starttls()
        s.login(self.config.smtp_address, self.config.smtp_pwd)

        return s

    def get_message_body(self, heading: str, immos: [CrawledImmo]) -> str:
        if len(immos) == 0:
            return ""
        body = heading
        immo: CrawledImmo
        entry_delimiter_template = "-------------"
        for immo in immos:
            open_spaces = []
            if immo.has_garden:
                open_spaces.append("G")
            if immo.has_balcony:
                open_spaces.append("B")
            if immo.has_loggia:
                open_spaces.append("L")
            if immo.has_terrace:
                open_spaces.append("T")
            entry_delimiter: str
            entry_delimiter = (entry_delimiter_template[:2]
                               + immo.provider
                               + entry_delimiter_template[len(immo.provider) + 2:])
            body = (body + "\n" + entry_delimiter + "\n" +
                    ", ".join((immo.postcode, immo.city, immo.street)) + "\n" +
                    str(immo.rooms).replace(".", ",") + " Zimmer / " + str(immo.surface).replace(".", ",")
                    + " m² / Freiflächen: " + "/".join(open_spaces)
                    + "\nMiete: " + str(immo.rent).replace(".", ",") + "€ / Eigenmittel: " +
                    str(immo.self_funding).replace(".", ",") + " €\nStatus: " + immo.status + "\n" + immo.detail_url
                    )

        return body
