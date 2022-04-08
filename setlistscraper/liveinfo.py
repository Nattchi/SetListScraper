class LiveInfo:
    def __init__(self):
        self.live_title = ""
        self.title = ""
        self.date = ""
        self.place = ""
        self.url = ""
        self.setlist = dict()

    def __dict__(self):
        return {
            "live_title": self.live_title,
            "title": self.title,
            "date": self.date,
            "place": self.place,
            "url": self.url,
            "setlist": self.setlist,
        }


def new_liveinfo_dict():
    return LiveInfo().__dict__()
