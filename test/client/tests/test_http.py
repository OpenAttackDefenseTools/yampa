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
            return None

        try:
            data = response.json()
        except:
            pass
        else:
            if ("^TESTFLAG_[A-Z]{20}$", data['flag']):
                raise AssertionError("Expected flag from `/genericwebsite/flagstore` to be caught")
            else:
                pass

    else: # non-filter
        response = http_session.get("/genericwebsite/flagstore", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])

        print(data)

def test_filter_engine_catch_flag_if_login(is_filtered, http_session):
    if is_filtered:
        # if the username is set but `login` was _not_ visited, you should get a flag
        response = http_session.get("/genericwebsite/flagstore?user=exampleuserA", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert 'flag' in data.keys()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])

        # logging in
        response = http_session.get("/genericwebsite/login", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert 'login-success' in data.keys()

        # but if a user is set and `login` was visited, the flag should be dropped
        try:
            response = http_session.get(f"/genericwebsite/flagstore?user=exampleuserB", timeout=0.5)
        except RequestException:
            return None

        try:
            data = response.json()
        except:
            pass
        else:
            if re.match("^TESTFLAG_[A-Z]{20}$", data['flag']):
                raise AssertionError("Expected flag from `/genericwebsite/flagstore` to be dropped")
            else:
                return None

    else:
        response = http_session.get("/genericwebsite/login", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert 'login-success' in data.keys()

        response = http_session.get(f"/genericwebsite/flagstore?user=exampleuser", timeout=0.5)
        assert response.status_code == 200
        data = response.json()
        assert re.match("^TESTFLAG_[A-Z]{20}$", data['flag'])

        print(data)


