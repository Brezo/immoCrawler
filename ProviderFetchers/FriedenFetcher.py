from ImmoCrawler import ImmoFetcher, CrawledImmo, CrawlerConfig
import requests
from bs4 import BeautifulSoup
import re


class FriedenFetcher(ImmoFetcher):
    provider = "FRIEDEN"

    def __init__(self, provider, config: CrawlerConfig):
        self.__page = 0
        self.__max_page = 0
        self.__config = config

    def fetch(self) -> [CrawledImmo]:
        immo_results = []
        self.__max_page = 0
        self.__page = 1
        while (self.__max_page == 0 or
               self.__page <= self.__max_page):
            # print("page: " + str(self.__page) + "/" + str(self.__max_page))
            for result in self.__get_search_results():
                immo_results.append(result)
            self.__page = self.__page + 1
        return immo_results

    def __get_search_results(self) -> [CrawledImmo]:
        immo_results = []
        surface_filter_from = "_"
        surface_filter_to = "_"
        if self.__config.surface_min > 0:
            surface_filter_from = str(self.__config.surface_min)

        if self.__config.surface_max > 0:
            surface_filter_to = str(self.__config.surface_max)

        url = "https://www.frieden.at/immobiliensuche/GetAll?ty=Flat&cs=constructed&st=Wien&st=Niederösterreich&ar=" \
               + surface_filter_from + "-" + surface_filter_to + "&pg=" + str(self.__page)

        r = requests.get(url)
        response_json = r.json()

        if self.__max_page == 0:
            self.__max_page = response_json["pageCount"]

        for item in response_json["items"]:
            immo = CrawledImmo()
            immo.provider = "FRIEDEN"
            immo.id = str(item["id"])
            immo.detail_url = "https://www.frieden.at/immobiliensuche/" + immo.id

            immo.postcode = item["postCode"]
            if not self.__check_postcode_in_filter(str(immo.postcode)):
                continue

            immo.street = item["street"]
            if item["staircase"] != '':
                immo.street = immo.street + ' / ' + item["staircase"]

            if item["label"] != '':
                immo.street = immo.street + ' / ' + item["label"]

            immo.city = item["city"]
            immo.rooms = item["numberOfRooms"]
            if immo.rooms is None:
                immo.rooms = 0
            immo.surface = item["usableArea"]

            financing = item["financingOptions"][0]
            if financing["ownResources"] != 0:
                immo.self_funding = financing["ownResources"]
            elif financing["deposit"] != 0:
                immo.self_funding = financing["deposit"]
            if immo.self_funding is None:
                immo.self_funding = 0.0

            if financing["paymentDemand"] != 0:
                immo.rent = financing["paymentDemand"]
            elif financing["price"] != 0:
                immo.rent = financing["price"]

            # get single results from response
            immo_results.append(self.__get_immo_open_spaces(immo))

        return immo_results

    def __check_postcode_in_filter(self, postcode: str):
        if self.__config.postcode_filter == '':
            #no filter, accept every postcode
            return True

        if re.search(self.__config.postcode_filter, postcode) is None:
            return False
        else:
            return True


    def __get_immo_open_spaces(self, immo: CrawledImmo) -> CrawledImmo:
        """check flat for open spaces"""
        response = requests.get(immo.detail_url)
        doc = BeautifulSoup(response.text, "html.parser")

        for features in doc.select("div.kJYuCe div"):
            if "garten" in features.text.lower():
                immo.has_garden = True
            elif "balkon" in features.text.lower():
                immo.has_balcony = True
            elif "terasse" in features.text.lower():
                immo.has_terrace = True
            elif "loggia" in features.text.lower():
                immo.has_terrace = True

        return immo
