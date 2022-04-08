class ArtistInfo:
    def __init__(self, artist=""):
        self.artist = artist
        self.artist_url = ""
        self.event_url = list()
        self.event_title = list()
        self.live_info_dict = dict()

    def __dict__(self):
        return {
            "artist": self.artist,
            "artist_url": self.artist_url,
            "event_url": self.event_url,
            "event_title": self.event_title,
            "live_info_dict": self.live_info_dict,
        }

    def add_live_info(self, live_info):
        self.live_info_dict[live_info["live_title"]] = live_info
