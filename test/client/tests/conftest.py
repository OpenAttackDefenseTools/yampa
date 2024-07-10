import os
import tempfile

import pytest

from requests import Session


class BaseUrlSession(Session):
    def __init__(self, base_url=None, *args, **kwargs):
        super(BaseUrlSession, self).__init__(*args, **kwargs)
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        return super(BaseUrlSession, self).request(method, self.base_url + url, *args, **kwargs)


@pytest.fixture(scope="session", params=["filtered", "unfiltered"])
def is_filtered(request):
    return request.param == "filtered"


@pytest.fixture(scope="session")
def hostname(is_filtered):
    return "10.2.3.4" if is_filtered else "testserver"  # if os.environ["YAMPA_TEST_CLIENT"] == "outside" else "10.2.3.4"

@pytest.fixture(scope="session", params=["withLogin", "withoutLogin"])
def do_login(request):
    return request.param == "withLogin"

@pytest.fixture(scope="session", params=["http", "https"])
def http_session(request, hostname):
    if request.param == "http":
        with BaseUrlSession(base_url=f"http://{hostname}") as session:
            yield session
    else:
        with tempfile.NamedTemporaryFile("w") as certfile:
            certfile.write(os.environ["HTTPS_CERTIFICATE"])
            certfile.flush()
            with BaseUrlSession(base_url=f"https://{hostname}") as session:
                session.verify = certfile.name
                yield session
