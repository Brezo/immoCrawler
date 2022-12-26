import re

from .CrawledImmo import CrawledImmo
from .CrawlerConfig import CrawlerConfig


class ImmoFetcher:
    status_removed = 'removed'
    status_available = 'available'
    status_reserved = 'reserved'
    status_under_construction = 'construction'

    def __new__(cls, provider: str, config: CrawlerConfig):
        subclass_map = {subclass.provider: subclass for subclass in cls.__subclasses__()}
        subclass = subclass_map[provider]
        instance = super(ImmoFetcher, subclass).__new__(subclass)
        return instance
    """
        https://stackoverflow.com/questions/7273568/pick-a-subclass-based-on-a-parameter/60769071#60769071
    """

    def fetch(self) -> [CrawledImmo]:
        pass

    def _amount_str_to_float(amount_text: str) -> float:
        """
        Remove thousands separator, euro sign, unsupported characters
        Replace decimal separator , -> .
        :return:
        Float number converted from string.
        """
        return float(amount_text.replace(".", "").replace(",", ".").replace("€","").replace(u'\xa0', ''))

    def _check_postcode_in_filter(config: CrawlerConfig, postcode: str):
        if config.postcode_filter == '':
            #no filter, accept every postcode
            return True

        if re.search(config.postcode_filter, postcode) is None:
            return False
        else:
            return True

    def _check_surface_in_filter(config: CrawlerConfig, area: float) -> bool:
        # check if apartment matches filter criteria
        if (config.surface_min <= area <= config.surface_max != 0)\
                or (config.surface_min <= area and config.surface_max == 0):
            return True
        else:
            return False
