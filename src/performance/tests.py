"""Performance benchmarking tests for InvenTree using the module."""

import json
import os

import pytest
from inventree.api import InvenTreeAPI

server = os.environ.get('INVENTREE_PYTHON_TEST_SERVER', 'http://127.0.0.1:12345')
user = os.environ.get('INVENTREE_PYTHON_TEST_USERNAME', 'testuser')
pwd = os.environ.get('INVENTREE_PYTHON_TEST_PASSWORD', 'testpassword')
api_client = InvenTreeAPI(
    server,
    username=user,
    password=pwd,
    timeout=30,
    token_name='python-test',
    use_token_auth=True,
)


@pytest.mark.benchmark
def test_api_auth_performance():
    """Benchmark the API authentication performance."""
    client = InvenTreeAPI(
        server,
        username=user,
        password=pwd,
        timeout=30,
        token_name='python-test',
        use_token_auth=True,
    )
    assert client


@pytest.mark.benchmark
@pytest.mark.parametrize(
    'url',
    [
        '/api/part/',
        '/api/part/category/',
        '/api/stock/',
        '/api/stock/location/',
        '/api/company/',
        '/api/build/',
        #'/api/build/line/',
        '/api/build/item/',
        '/api/order/so/',
        '/api/order/so/shipment/',
        #'/api/order/po/',
        #'/api/order/po-line/',
        '/api/user/roles/',
        '/api/parameter/',
        '/api/parameter/template/',
    ],
)
def test_api_list_performance(url):
    """Benchmark the API list request performance."""
    result = api_client.get(url)
    assert result
    assert len(result) > 0


@pytest.mark.benchmark
@pytest.mark.parametrize(
    'url',
    [
        '/api/part/',
        '/api/part/category/',
        '/api/stock/location/',
        '/api/company/',
        '/api/build/',
        '/api/build/line/',
        '/api/build/item/',
        '/api/order/so/',
        '/api/order/so/shipment/',
        '/api/order/po/',
        '/api/order/po-line/',
        '/api/user/roles/',
        '/api/parameter/',
        '/api/parameter/template/',
    ],
)
def test_api_options_performance(url):
    """Benchmark the API OPTIONS request performance."""
    response = api_client.request(url, method='OPTIONS')
    result = json.loads(response.text)
    assert result
    assert 'actions' in result
    assert len(result['actions']) > 0
