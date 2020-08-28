# Exception raised if user provides a series name that is not valid on MangaReader.net.
class InvalidSeriesProvided(Exception):
    pass
# Exception raised if status code != 200
class BadStatusCodeError(Exception):
    pass
# Exception raised if HTTP status code is 520 - Unknown error
class StatusCode520Error(Exception):
    pass
# Exception raised if HTTP status code is 522 - Timeout error
class StatusCode522Error(Exception):
    pass