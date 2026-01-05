"""Performance benchmarking tests for InvenTree using the module."""

import os

import pytest

from inventree.api import InvenTreeAPI

host = os.getenv('INVENTREE_PYTHON_TEST_SERVER')
api_client = InvenTreeAPI(host=host)


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
def test_api_list_performance(url):
    """Benchmark the fibonacci function for various n values."""
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
    url = '/api/part/'
    result = api_client.request(url, method='OPTIONS')
    assert result
    assert 'actions' in result
    assert len(result['actions']) > 0
