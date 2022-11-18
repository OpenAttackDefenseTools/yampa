import re

from requests.exceptions import *


def test_basic_response(http_session, https_session):
    for session in (http_session, https_session):
        response = session.get("/", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert data['hello'] == 'world'


def test_legitimate(http_session, https_session):
    for session in (http_session, https_session):
        response = session.get("/legitimate", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("TESTFLAG_[A-Z]{20}", data['flag'])


def test_exploit(is_filtered, http_session, https_session):
    for session in (http_session, https_session):
        if is_filtered:
            try:
                response = session.get("/exploit/AAAAAAAAAAAAAAAAAAAAAAA", timeout=0.5)
            except ReadTimeout:
                pass
            else:
                raise AssertionError("Expected /exploit to fail")
        else:
            response = session.get("/exploit/AAAAAAAAAAAAAAAAAAAAAAA", timeout=0.5)
            assert response.status_code == 200
            data = response.json()
            assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])
