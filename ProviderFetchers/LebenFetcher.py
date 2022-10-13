from ImmoCrawler import ImmoFetcher, CrawledImmo, CrawlerConfig
import re
import requests
from bs4 import BeautifulSoup


class LebenFetcher(ImmoFetcher):
    provider = "LEBEN"

    def __init__(self, provider: str, config: CrawlerConfig):
        self.__config = config

    def fetch(self) -> [CrawledImmo]:
        immo_results = []
        overview_cards = self.__get_cards()
        doc = BeautifulSoup(overview_cards.text, "html.parser")

        for result_card in doc.select("a.unstyled"):
            # resolve object details from response
            object_path = result_card.get('href')
            for apartment in self.__resolve_building(object_path):
                immo_results.append(apartment)
        return immo_results

    def __resolve_building(self, object_path: str):
        url = 'https://www.wohnen.at' + object_path
        immo_results = []
        crawled_immo: CrawledImmo

        r = requests.get(url)
        doc = BeautifulSoup(r.text, "html.parser")
        zip_city_pattern = "(\d{4}) (.+)(?=,.+)"
        building_address = doc.select_one("div.building-page h1").text
        address_result = re.findall(zip_city_pattern, building_address)

        for apartment in doc.select("div.row.mobile-filter-row div.col-md-12"):
            crawled_immo = CrawledImmo()
            crawled_immo.city = address_result[0][1]
            crawled_immo.postcode = address_result[0][0]
            if not self.__check_postcode_in_filter(str(crawled_immo.postcode)):
                continue
            area = float(apartment.select_one("span.area").text.replace(",", "."))
            if not self.__check_area_in_filter(area):
                continue

            id = re.findall("(?<=location.href='/angebot/wohnung-detail/\?id=).+(?=')", apartment.get("onclick"))
            if id is None:
                continue

            crawled_immo.id = id[0]
            crawled_immo.provider = self.provider
            crawled_immo.surface = area
            crawled_immo.rooms = float(apartment.select_one("span.room").text)
            crawled_immo.street = apartment.select_one("span.address").text
            crawled_immo.self_funding = self.__amount_str_to_float(apartment.select_one(
                "span.financing-option-value").text)

            immo_results.append(self.__get_apartment_details(crawled_immo))

        return immo_results

    def __check_postcode_in_filter(self, postcode: str):
        if self.__config.postcode_filter == '':
            #no filter, accept every postcode
            return True

        if re.search(self.__config.postcode_filter, postcode) is None:
            return False
        else:
            return True

    def __get_apartment_details(self, crawled_immo: CrawledImmo) -> CrawledImmo:
        crawled_immo.detail_url = "https://www.wohnen.at/angebot/wohnung-detail/?id=" + crawled_immo.id
        r = requests.get(crawled_immo.detail_url)
        doc = BeautifulSoup(r.text, "html.parser")

        for financing in doc.select("div.financing-variant-row"):
            if "monatliche Kosten" in financing.select_one("div.col-md-4.col-sm-6.col-xs-12.financing-title").text:
                crawled_immo.rent = self.__amount_str_to_float(
                                        financing.select_one("div.col-md-3.col-sm-6.col-xs-12.financing-value").text)

        for feature in doc.select("div.row.equipment-row div.col-md-6 div"):
            if "garten" in feature.text.lower():
                crawled_immo.has_garden = True
            elif "loggia" in feature.text.lower():
                crawled_immo.has_loggia = True
            elif "balkon" in feature.text.lower():
                crawled_immo.has_balcony = True
            elif "terasse" in feature.text.lower():
                crawled_immo.has_terrace = True

        return crawled_immo

    def __check_area_in_filter(self, area: float) -> bool:
        # check if apartment matches filter criteria
        if (self.__config.surface_min <= area <= self.__config.surface_max != 0)\
                or (self.__config.surface_min <= area and self.__config.surface_max == 0):
            return True
        else:
            return False

    def __get_cards(self) -> requests.Response:
        url = "https://www.wohnen.at/umbraco/Surface/UnitSearch/Filter"

        payload = 'FilterState.IsCompletedChecked=true&FilterState.IsCompletedChecked=false&FilterState' \
                  '.IsInConstructionChecked=false&FilterState.IsPlannedChecked=false&FilterState.IsRentalChecked' \
                  '=false&FilterState.IsOwnershipChecked=false&X-Requested-With=XMLHttpRequest&FilterState' \
                  '.DistrictChecked.Index=0 '
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        return requests.request("POST", url, headers=headers, data=payload)

    def __amount_str_to_float(self, amount_text: str) -> float:
        return float(amount_text.replace(",", ".").replace("€","").replace(u'\xa0', ''))
