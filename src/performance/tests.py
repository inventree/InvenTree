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


@pytest.mark.benchmark
@pytest.mark.parametrize(
    'key',
    [
        'all',
        'part',
        'partcategory',
        'supplierpart',
        'manufacturerpart',
        'stockitem',
        'stocklocation',
        'build',
        'supplier',
        'manufacturer',
        'customer',
        'purchaseorder',
        'salesorder',
        'salesordershipment',
        'returnorder',
    ],
)
def test_search_performance(key: str):
    """Benchmark the API search performance."""
    SEARCH_URL = '/api/search/'

    # An indicative search query for various model types
    SEARCH_DATA = {
        'part': {'active': True},
        'partcategory': {},
        'supplierpart': {
            'part_detail': True,
            'supplier_detail': True,
            'manufacturer_detail': True,
        },
        'manufacturerpart': {
            'part_detail': True,
            'supplier_detail': True,
            'manufacturer_detail': True,
        },
        'stockitem': {'part_detail': True, 'location_detail': True, 'in_stock': True},
        'stocklocation': {},
        'build': {'part_detail': True},
        'supplier': {},
        'manufacturer': {},
        'customer': {},
        'purchaseorder': {'supplier_detail': True, 'outstanding': True},
        'salesorder': {'customer_detail': True, 'outstanding': True},
        'salesordershipment': {},
        'returnorder': {'customer_detail': True, 'outstanding': True},
    }

    model_types = list(SEARCH_DATA.keys())

    search_params = SEARCH_DATA if key == 'all' else {key: SEARCH_DATA[key]}

    # Add in a common search term
    search_params.update({'search': '0', 'limit': 50})

    response = api_client.post(SEARCH_URL, data=search_params)
    assert response

    if key == 'all':
        for model_type in model_types:
            assert model_type in response
            assert 'error' not in response[model_type]
    else:
        assert key in response
        assert 'error' not in response[key]
