class CrawledImmo():
    def __init__(self, id="", postcode="", street="",
                 surface=0.0, rent=0.0, rooms=0.0,
                 self_funding=0.0, city="", status="",
                 has_garden=False, has_loggia=False, has_balcony=False,
                 has_terrace=False, provider="", detail_url=""):
        self.id = id
        self.postcode = postcode
        self.street = street
        self.surface = surface
        self.rent = rent
        self.rooms = rooms
        self.city = city
        self.status = status
        self.self_funding = self_funding
        self.has_garden = has_garden
        self.has_loggia = has_loggia
        self.has_balcony = has_balcony
        self.has_terrace = has_terrace
        self.provider = provider
        self.detail_url = detail_url
