from ImmoCrawler import ImmoFetcher, CrawledImmo, CrawlerConfig
import re
import requests
from urllib.parse import urlparse
from urllib.parse import parse_qs
from bs4 import BeautifulSoup


class OESWFetcher(ImmoFetcher):
    provider = "OESW"
    base_url = "https://www.oesw.at"

    def __init__(self, provider: str, config: CrawlerConfig):
        # self.__page = 0
        # self.__max_page = 0
        self.__config = config

    def fetch(self) -> [CrawledImmo]:
        immo_results = []
        self.__page = 1

        # get available objects
        r = requests.get( self.base_url + "/immobilienangebot/sofort-wohnen.html?objectType=0")
        doc = BeautifulSoup(r.text, "html.parser")
        available_buildings = doc.select("ul.og-grid li a")
        for available_building in available_buildings:
            # check target url (either oesw.at or relative path, no external links)
            target_link = available_building.get("href")
            if target_link[0] != '/' and 'oesw.at' not in target_link:
                continue

            # check if postcode matches regex from config
            if self.__config.postcode_filter:
                city = available_building.get("data-title")
                regex_results = re.findall("\d{4}", city)
                if re.match(self.__config.postcode_filter, regex_results[0]) is None:
                    continue

            for immo in self.__get_objects_at_address(self.base_url + target_link):
                immo_results.append(immo)

        return immo_results

    def __get_objects_at_address(self, address_link) -> [CrawledImmo]:
        immo_results = []

        # get available objects of address/building
        r = requests.get(address_link)
        doc = BeautifulSoup(r.text, "html.parser")

        """get units embedded into page"""
        data_url = doc.select_one("#objList").get("data-action")
        form_data = {"tx_mhimmo_pi1[withFilter]": True, "tx_mhimmo_pi1[offset]": 0, "tx_mhimmo_pi1[limit]": 10}
        units_data = requests.post(self.base_url + data_url, data=form_data)
        units_json = units_data.json()
        units_doc = BeautifulSoup(units_json["content"], "html.parser")
        for unit in units_doc.select("a.anim"):
            object_type = unit.select_one("div.desc-2")
            # only process apartments, no garages or office spaces
            if "Wohnung" not in object_type.text:
                continue

            unit_url = unit.get("href")
            object_detail = self.__get_object_details(self.base_url + unit_url)
            if object_detail is None:
                continue

            immo_results.append(object_detail)

        return immo_results

    def __get_object_details(self, detail_link: str) -> CrawledImmo:
        amount_pattern = '€ ((?:\d{0,3}\.?)*,?\d{0,2})'
        staircase = ''
        door_nr = ''
        object_detail = CrawledImmo()
        r = requests.get(detail_link)
        doc = BeautifulSoup(r.text, "html.parser")

        parsed_url = urlparse(detail_link)
        object_detail.id = parse_qs(parsed_url.query)['tx_mhimmo_pi1[erpId]'][0]
        object_detail.detail_url = detail_link
        object_detail.provider = self.provider

        postcode_city = doc.select_one("span.adr-1")
        postcode_match = re.match("(\d{4}) (.+)", postcode_city.text)
        if postcode_match is None:
            return None

        object_detail.postcode = postcode_match.group(1)
        object_detail.city = postcode_match.group(2)
        object_detail.street = doc.select_one("h2.adr-2").text
        if 'sofort verfügbar' in doc.select_one("section.labelWrapper span.label-2").text:
            object_detail.status = 'available'
        else:
            object_detail.status = 'other'

        key_data = doc.select_one("section.eckdaten div.row")
        for immo_detail in key_data.select("div.col-sm-4 div"):
            nav_string = str(immo_detail.contents[1])
            label_txt = immo_detail.select_one("strong.dark").text
            if 'Stiege' in label_txt:
                staircase = nav_string

            if 'Top' in label_txt:
                door_nr = nav_string

            if 'Größe' in label_txt:
                """surface uses different index due of exponent"""
                size_match = re.match('(\d+\.?\d{0,2})m', str(immo_detail.contents[2]))
                if size_match is None:
                    return None

                object_detail.surface = float(size_match.group(1))
                if not self.__check_surface_in_filter(object_detail.surface):
                    return None

            if 'Zimmer' in label_txt:
                object_detail.rooms = float(nav_string)

        if staircase != '':
            object_detail.street = object_detail.street + '/' + staircase

        if door_nr != '':
            object_detail.street = object_detail.street + '/' + door_nr

        for pricing_detail in key_data.select("div.col-sm-8 div.fVar div"):
            if len(pricing_detail.contents) > 1:
                nav_string = str(pricing_detail.contents[2])
            label_txt = pricing_detail.select_one("strong.dark").text

            if 'Kosten' in label_txt:
                self_funding_match = re.match(amount_pattern, nav_string)
                if self_funding_match is None:
                    return None
                object_detail.self_funding = self_funding_match.group(1).replace('.', '').replace(',', '.')

            if 'Kosten pro Monat' in label_txt:
                rent_match = re.match(amount_pattern, nav_string)
                if rent_match is None:
                    return None
                object_detail.rent = rent_match.group(1).replace('.', '').replace(',', '.')

        return object_detail

    def __check_surface_in_filter(self, area: float) -> bool:
        # check if apartment matches filter criteria
        if (self.__config.surface_min <= area <= self.__config.surface_max != 0)\
                or (self.__config.surface_min <= area and self.__config.surface_max == 0):
            return True
        else:
            return False
