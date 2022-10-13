from .CrawledImmo import CrawledImmo
from .CrawlerConfig import CrawlerConfig


class ImmoFetcher:

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
