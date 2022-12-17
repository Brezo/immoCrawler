from ImmoCrawler import ImmoFetcher, CrawledImmo, CrawlerConfig
import re
import requests
from bs4 import BeautifulSoup


class NHGFetcher(ImmoFetcher):
    provider = "NHG"

    def __init__(self, provider: str, config: CrawlerConfig):
        self.__page = 0
        self.__max_page = 0
        self.__config = config

    def fetch(self) -> [CrawledImmo]:
        immo_results = []
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

        url = "https://nhg.at/umbraco/Surface/LivingUnits/Step?page=" + str(self.__page)
        if self.__config.surface_min > 0:
            url = url + "&squareMetersFrom=" + str(self.__config.surface_min)
        if self.__config.surface_max > 0:
            url = url + "&squareMetersTo=" + str(self.__config.surface_max)

        r = requests.post(url)
        doc = BeautifulSoup(r.text, "html.parser")
        if self.__max_page == 0:
            m = re.search("(?<=von )\d+(?= Seiten)", doc.text)
            if m:
                self.__max_page = int(m.group(0))
            else:
                self.__max_page = 1

        for result_card in doc.select("div.panel"):
            #get postcode and check filter
            if not self.__check_postcode_in_filter(result_card.select_one("h5").text[0:4]):
                continue
            # get single results from response
            detail_path = result_card.get('data-url')
            immo_results.append(self.__get_immo_detail(detail_path))
        return immo_results

    def __check_postcode_in_filter(self, postcode: str):
        if self.__config.postcode_filter == '':
            #no filter, accept every postcode
            return True

        if re.search(self.__config.postcode_filter, postcode) is None:
            return False
        else:
            return True

    def __get_immo_detail(self, detail_url) -> CrawledImmo:

        url = "https://nhg.at/" + detail_url
        r = requests.get(url)
        doc = BeautifulSoup(r.text, "html.parser")

        # parse address
        address = doc.select_one("div.header p")
        split_adr = address.text.split(",")
        immo = CrawledImmo()
        immo.provider = self.provider

        m = re.search("(?<=offerId=)\d+", detail_url)
        immo.id = m.group(0)

        immo.street = split_adr[1]
        split_city = split_adr[0].split()
        immo.postcode = split_city[0]
        immo.city = split_city[1]
        immo.detail_url = url

        # get status (being built, available, reserved)
        status = doc.select_one("span.detail-label")
        if status:
            immo.status = status.text

        surface = doc.select_one("div.qm").text

        immo.surface = float(str(surface).replace(",", "."))

        # get immo details from 'Details' area (size, rooms, ...)
        detail = doc.select_one("div#Details")
        for detail_list in detail.select("div.row"):
            for detail_element in detail_list.select("div.columns"):
                if "Garten" in detail_element.text:
                    immo.has_garden = True
                elif "Terrasse" in detail_element.text:
                    immo.has_terrace = True
                elif "Balkon" in detail_element.text:
                    immo.has_balcony = True
                elif "Loggia" in detail_element.text:
                    immo.has_loggia = True
                elif "zimmeranzahl" in detail_element.text.lower():
                    try:
                        immo.rooms = float(detail_element.findNext("div").contents[0])
                    except ValueError:
                        pass

        # get rent, self-funding...
        finance = doc.select_one("div#Finanzierung")
        for finance_detail in finance.select("div.euro"):
            finance_label = finance_detail.parent.findPrevious("div").contents[0]
            amount_sanitized = finance_detail.text.replace(u'\xa0', '').replace(",", ".")
            if "Belastung" in finance_label:
                immo.rent = float(amount_sanitized)
            if "Kaution" in finance_label or "Eigenmittel" in finance_label:
                immo.self_funding = float(amount_sanitized)
        return immo
