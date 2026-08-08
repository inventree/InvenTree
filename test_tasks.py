"""Tests for the root Invoke tasks."""

import importlib
from urllib.parse import urlparse

import pytest
import tasks
from invoke import Context
from invoke.exceptions import Exit


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ('site_url', 'allowed_host', 'healthy'),
    [
        (None, None, True),
        ('https://inventory.example.com', 'inventory.example.com', True),
        ('https://inventory.example.com', 'other.example.com', False),
    ],
)
def test_server_health_hosts(
    live_server, settings, monkeypatch, site_url, allowed_host, healthy
):
    """Test site URL host selection against Django's allowed hosts."""
    address_host = urlparse(live_server.url).hostname
    settings.ALLOWED_HOSTS = [allowed_host or address_host]

    config = importlib.import_module('src.backend.InvenTree.InvenTree.config')
    monkeypatch.setattr(config, 'get_setting', lambda *args: site_url)

    def check_health():
        tasks.server_health.body(Context(), address=live_server.url, timeout=2)

    if healthy:
        check_health()
    else:
        with pytest.raises(Exit) as exc:
            check_health()

        assert exc.value.code == 1
