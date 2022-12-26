from ImmoCrawler import ImmoFetcher, CrawledImmo, CrawlerConfig
import re
import requests
from bs4 import BeautifulSoup


class SozialbauFetcher(ImmoFetcher):

    provider = "SOZIALBAU"

    def __init__(self, provider: str, config: CrawlerConfig):
        self.__config = config

    def fetch(self) -> [CrawledImmo]:
        available_immo = self.__get_available_immo()

        return available_immo

    def __get_available_immo(self) -> [CrawledImmo]:

        base_url = 'https://www.sozialbau.at'
        available_immo = []
        crawled_immo: CrawledImmo
        postcode = ''
        resp = requests.get(base_url + '/angebot/sofort-verfuegbar/')
        doc = BeautifulSoup(resp.text, "html.parser")

        for apartment in doc.select("form.mobile-table table tbody tr"):
            #get data from columns
            column_counter = 0
            crawled_immo = CrawledImmo()
            for column in apartment.select("td"):

                crawled_immo.provider = self.provider
                column_counter += 1

                if column_counter == 1:
                    crawled_immo.detail_url = base_url + column.select_one("a").get("href")
                    id = re.findall("Hash=(.+)", crawled_immo.detail_url)
                    if id is not None:
                        crawled_immo.id = id[0]
                    #address will be determined from detail page
                    postcode = column.text
                    postcode = postcode.replace("\n", "").replace("\t", "")[0:4]
                elif column_counter == 2:
                    crawled_immo.rooms = int(column.text)
                elif column_counter == 3:
                    crawled_immo.self_funding = ImmoFetcher._amount_str_to_float(column.text)
                elif column_counter == 4:
                    crawled_immo.rent = ImmoFetcher._amount_str_to_float(column.text)
                else:
                    break

            if not ImmoFetcher._check_postcode_in_filter(self.__config, postcode):
                continue

            if len(crawled_immo.detail_url) > 0 and len(crawled_immo.id) > 0:
                self.__get_detail(crawled_immo)
            else:
                continue

            if not ImmoFetcher._check_surface_in_filter(self.__config, crawled_immo.surface):
                continue

            available_immo.append(crawled_immo)

        return available_immo

    def __get_detail(self, crawled_immo:CrawledImmo):
        address_pattern = '(\d{4}) (.+), (.*)'
        resp = requests.get(crawled_immo.detail_url)
        doc = BeautifulSoup(resp.text, "html.parser")

        details = doc.select_one("div.tx-wx-sozialbau div.container")
        address = re.findall(address_pattern, details.select_one("h1").text)
        if address is not None:
            crawled_immo.postcode = address[0][0]
            crawled_immo.city = address[0][1]
            crawled_immo.street = address[0][2]

        for item in details.select("ul li"):
            if "m²" in item.text:
                surface = re.findall("\d+", item.text)
                if surface is not None:
                    crawled_immo.surface = float(surface[0])
