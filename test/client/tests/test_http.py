import re

from requests.exceptions import *


def test_basic_response(http_session):
    response = http_session.get("/", timeout=0.5)
    assert response.status_code == 200
    data = response.json()
    assert data['hello'] == 'world'


def test_legitimate(http_session):
    response = http_session.get("/legitimate", timeout=0.5)
    assert response.status_code == 200
    data = response.json()
    assert re.match("TESTFLAG_[A-Z]{20}", data['flag'])


def test_exploit(is_filtered, http_session):
    if is_filtered:
        try:
            response = http_session.get("/exploit/AAAAAAAAAAAAAAAAAAAAAAA", timeout=0.5)
        except RequestException:
            pass
        else:
            raise AssertionError("Expected /exploit to fail")
    else:
        response = http_session.get("/exploit/AAAAAAAAAAAAAAAAAAAAAAA", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])

'''
    @brief: test that a flag can be retrieved iff precedet by a login
'''
def test_filter_engine_catch_flag(is_filtered, http_session):
    if is_filtered:

        # flag must not be retrievable if not logged in:
        try:
            response = http_session.get("/genericwebsite/flagstore", timeout=0.5)
        except RequestException:
            pass
        else:
            raise AssertionError("Expected flag from `/genericwebsite/flagstore` to be caught")

        # flag must be retrievable if logged in:
        response = http_session.get("/genericwebsite/login", timeout=0.5)
        assert response.status_code == 200

        response = http_session.get("/genericwebsite/flagstore", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])

    else:
        response = http_session.get("/genericwebsite/login", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert data['loggedin'] == True

        response = http_session.get("/genericwebsite/flagstore", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])
