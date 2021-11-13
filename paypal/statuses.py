from rest_framework import status


def get_rest_framework_status(http_code: int):
    statuses = {
        100: {
            100: status.HTTP_100_CONTINUE,
            101: status.HTTP_101_SWITCHING_PROTOCOLS
        },
        200: {
            200: status.HTTP_200_OK,
            201: status.HTTP_201_CREATED,
            202: status.HTTP_202_ACCEPTED,
            203: status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,
            204: status.HTTP_204_NO_CONTENT,
            205: status.HTTP_205_RESET_CONTENT,
            206: status.HTTP_206_PARTIAL_CONTENT
        },
        300: {
            300: status.HTTP_300_MULTIPLE_CHOICES,
            301: status.HTTP_301_MOVED_PERMANENTLY,
            302: status.HTTP_302_FOUND,
            303: status.HTTP_303_SEE_OTHER,
            304: status.HTTP_304_NOT_MODIFIED,
            305: status.HTTP_305_USE_PROXY
        },
        400: {
            400: status.HTTP_400_BAD_REQUEST,
            401: status.HTTP_401_UNAUTHORIZED,
            402: status.HTTP_402_PAYMENT_REQUIRED,
            403: status.HTTP_403_FORBIDDEN,
            404: status.HTTP_404_NOT_FOUND,
            405: status.HTTP_405_METHOD_NOT_ALLOWED,
            406: status.HTTP_406_NOT_ACCEPTABLE,
            407: status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED,
            408: status.HTTP_408_REQUEST_TIMEOUT,
            409: status.HTTP_409_CONFLICT,
            410: status.HTTP_410_GONE,
            411: status.HTTP_411_LENGTH_REQUIRED,
            412: status.HTTP_412_PRECONDITION_FAILED,
            413: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            414: status.HTTP_414_REQUEST_URI_TOO_LONG,
            415: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        },
        500: {
            500: status.HTTP_500_INTERNAL_SERVER_ERROR,
            501: status.HTTP_501_NOT_IMPLEMENTED,
            502: status.HTTP_502_BAD_GATEWAY,
            503: status.HTTP_503_SERVICE_UNAVAILABLE,
            504: status.HTTP_504_GATEWAY_TIMEOUT,
            505: status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED
        }
    }
    if http_code < 200:
        http_class = 100
    elif 200 <= http_code < 300:
        http_class = 200
    elif 300 <= http_code < 400:
        http_class = 300
    elif 400 <= http_code < 500:
        http_class = 400
    else:
        http_class = 500
    rest_status = statuses[http_class].get(http_code)
    if not rest_status:
        rest_status = statuses[http_class][http_class]
    return rest_status
