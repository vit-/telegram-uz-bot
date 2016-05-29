import re

from uz.client.jjdecode import JJDecoder


JJ_CODE_PATTERN = re.compile(';_gaq.push\(\[\'_trackPageview\'\]\);(.+)\(function')  # noqa
TOKEN_PATTERN = re.compile('localStorage.setItem\(\"gv-token\", \"(\w+)\"\);')


def parse_gv_token(page):
    jj_code = JJ_CODE_PATTERN.search(page)
    if jj_code is None:
        return
    jj_code = jj_code.groups()[0]
    parsed = JJDecoder(jj_code).decode()
    token = TOKEN_PATTERN.search(parsed)
    return token and token.groups()[0]
