"""Middleware for the audit app."""

import ipaddress

from auditlog.context import set_extra_data
from auditlog.middleware import AuditlogMiddleware

from audit.context import audit_request


class InvenTreeAuditlogMiddleware(AuditlogMiddleware):
    """Bind request context to audit log entries.

    Differences from the upstream AuditlogMiddleware:
    - The actor is not captured here, but resolved lazily (see audit.context)
    - The remote address is taken from REMOTE_ADDR only, and validated
      (upstream trusts the first X-Forwarded-For entry and X-Forwarded-Port as-is)
    - The correlation ID matches the structlog request ID (see audit.context.get_cid)
    """

    @staticmethod
    def _get_remote_addr(request):
        """Return the (validated) remote address for the request.

        An invalid value would otherwise cause every audited save to fail
        on databases with a native IP address column type (PostgreSQL 'inet').
        """
        remote_addr = request.META.get('REMOTE_ADDR')

        if not remote_addr:
            return None

        try:
            return str(ipaddress.ip_address(remote_addr.strip()))
        except ValueError:
            return None

    def get_extra_data(self, request):
        """Return the data to be attached to all log entries created during this request."""
        return {'remote_addr': self._get_remote_addr(request), 'remote_port': None}

    def __call__(self, request):
        """Process the request within the audit context."""
        with (
            audit_request(request),
            set_extra_data(context_data=self.get_extra_data(request)),
        ):
            return self.get_response(request)
