"""Helper functions for allauth MFA testing."""

from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal import auth as allauth_totp_auth


def get_codes(user):
    """Generate active TOTP and recovery codes for a user.

    Args:
        user: User instance

    Returns:
        Tuple of (TOTP Authenticator instance, list of recovery codes, TOTP secret)
    """
    secret = allauth_totp_auth.generate_totp_secret()
    totp_auth = allauth_totp_auth.TOTP.activate(user, secret).instance
    rc_auth = RecoveryCodes.activate(user).instance

    # Get usable codes
    rc_codes = rc_auth.wrap().get_unused_codes()
    return totp_auth, rc_codes, secret
