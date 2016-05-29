class UZException(Exception):
    pass


class FailedObtainToken(UZException):
    pass


class HTTPError(UZException):

    def __init__(self, status_code, body, data=None, json=None):
        self.status_code = status_code
        self.body = body
        self.data = data
        self.json = json
        super().__init__(
            'status code: {}, request data: {}, response body: {}'.format(
                status_code, data, body))


class BadRequest(HTTPError):
    pass


class ResponseError(HTTPError):
    pass


class ImproperlyConfigured(UZException):
    pass
