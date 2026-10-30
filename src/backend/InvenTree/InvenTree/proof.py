"""Functions to use HMAC and HKDF for a limited time proof of identity based on the instance ID."""

import functools
import hashlib
import hmac
import re
from datetime import datetime as dt
from datetime import timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from common.settings import get_global_setting
from InvenTree.helpers import str2bool

PROOF_NONCE_REGEX = re.compile(r'[A-Za-z0-9_-]{1,64}')


@functools.lru_cache
def _link_subkey(instance_id: str) -> bytes:
    """Use HKDF to calculate a subkey from the instance ID."""
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b'inventree-link-v1'
    ).derive(instance_id.encode('utf-8'))


def calculate_proof(
    nonce, instance: str | None = None, epoch: str | None = None
) -> str | None:
    """Return the proof for a nonce, optionally for a different instance ID."""
    if not nonce or not PROOF_NONCE_REGEX.fullmatch(nonce):
        return None

    if not str2bool(
        get_global_setting(
            'INVENTREE_LINK_PROOF', environment_key='INVENTREE_LINK_PROOF'
        )
    ):
        return None

    # Get or use instance id; ensure we do not trigger generation
    instance_id = (
        instance
        if instance
        else get_global_setting('INVENTREE_INSTANCE_ID', backup_value='', create=False)
    )
    if not instance_id:
        return None

    if epoch is None:
        epoch = dt.now(timezone.utc).strftime('%Y-%m')

    _message = (epoch + nonce).encode('utf-8')
    return hmac.new(
        _link_subkey(str(instance_id)), _message, hashlib.sha256
    ).hexdigest()[:32]
