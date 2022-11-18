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
    # TODO: Implement proxy and remove this skip
    if request.param == "filtered":
        pytest.skip("Proxy is not implemented yet")

    return request.param == "filtered"


@pytest.fixture(scope="session")
def hostname(is_filtered):
    return "10.2.3.4" if is_filtered else "testserver"  # if os.environ["YAMP_TEST_CLIENT"] == "outside" else "10.2.3.4"


@pytest.fixture(scope="session")
def http_session(hostname):
    with BaseUrlSession(base_url=f"http://{hostname}") as session:
        yield session


@pytest.fixture(scope="session")
def https_session(hostname):
    with tempfile.NamedTemporaryFile("w") as certfile:
        certfile.write(os.environ["HTTPS_CERTIFICATE"])
        certfile.flush()
        with BaseUrlSession(base_url=f"https://{hostname}") as session:
            session.verify = certfile.name
            yield session
