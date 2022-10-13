import psycopg2
from ImmoCrawler import CrawledImmo, ImmoNotificationService, CrawlerConfig


class ImmoDbWriter:
    def __init__(self, provider, config: CrawlerConfig):
        self.config = config
        self.provider = provider
        self.existing_immo = []

    def get_connection(self):
        return psycopg2.connect(dbname=self.config.database, user=self.config.db_user,
                                host=self.config.db_host, password=self.config.db_password)

    def get_existing_entries(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            values = (self.provider,)
            statement = """SELECT * FROM crawled_immo \nWHERE provider = %s"""

            if self.config.surface_min > 0:
                statement = statement + "\nAND surface >= %s"
                values = values + (self.config.surface_min,)

            if self.config.surface_max > 0:
                statement = statement + "\nAND surface <= %s"
                values = values + (self.config.surface_max,)
            cur.execute(statement, values)

            for result in cur.fetchall():
                existing_immo = CrawledImmo()

                existing_immo.provider = result[0].strip()
                existing_immo.id = result[1].strip()
                existing_immo.has_garden = result[2]
                existing_immo.has_terrace = result[3]
                existing_immo.has_loggia = result[4]
                existing_immo.has_balcony = result[5]
                existing_immo.status = result[6].strip()
                existing_immo.rooms = float(result[7])
                existing_immo.surface = float(result[8])
                existing_immo.rent = float(result[9])
                existing_immo.self_funding = float(result[10])
                existing_immo.postcode = result[11].strip()
                existing_immo.street = result[12].strip()
                existing_immo.city = result[13].strip()
                existing_immo.detail_url = result[16].strip()

                self.existing_immo.append(existing_immo)
            cur.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        finally:
            if conn is not None:
                conn.close()

    def insert_data(self, crawled_immo=[]):
        statement = """INSERT INTO 
                        crawled_immo(provider, id, 
                                     has_garden, has_terrace, has_loggia, has_balcony,
                                     status, rooms, surface, rent, self_funding, postcode,
                                     street, city, detail_url) 
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        values = []
        for immo in crawled_immo:
            values.append((immo.provider, immo.id, immo.has_garden, immo.has_terrace, immo.has_loggia, immo.has_balcony,
                           immo.status, immo.rooms, immo.surface, immo.rent, immo.self_funding,
                           immo.postcode, immo.street, immo.city, immo.detail_url,))
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.executemany(statement, values)
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

        finally:
            if conn is not None:
                conn.close()

    def update_data(self, crawled_immo=[]):
        statement = """UPDATE crawled_immo
                        SET status = %s
                        WHERE provider = %s
                        AND   id = %s"""

        try:
            conn = self.get_connection()
            cur = conn.cursor()

            for immo in crawled_immo:
                cur.execute(statement, (immo.status, immo.provider, immo.id))

            updated_rows = cur.rowcount
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

    def write_data(self, crawled_immo: [CrawledImmo], notification_service: ImmoNotificationService):
        immo_insert = []
        immo_update = []

        self.get_existing_entries()


        # check if immo already saved, update if status changed
        for immo in crawled_immo:
            prev_immo = next((x for x in self.existing_immo if immo.provider == x.provider and immo.id == x.id), None)
            if prev_immo is None:
                immo_insert.append(immo)
            elif prev_immo.status != immo.status:
                immo_update.append(immo)

        # check if existing immo was removed
        for immo in self.existing_immo:
            if immo.status == "removed":
                continue
            prev_immo = next((x for x in crawled_immo if (immo.provider == x.provider and
                                                          immo.id == x.id)), None)
            if prev_immo is None:
                immo_update.append(CrawledImmo(provider=immo.provider, id=immo.id, status="removed"))

        if len(immo_insert) > 0:
            self.insert_data(immo_insert)
            print("INSERT: " + str(len(immo_insert)))

        if len(immo_update) > 0:
            self.update_data(immo_update)
            print("UPDATE: " + str(len(immo_update)))

        if notification_service:
            notification_service.add_immo(immo_insert, immo_update)
