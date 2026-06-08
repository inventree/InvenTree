"""
InvenTree/order/urls.py

Register API endpoints for Repair Orders.
Extends the existing order management system with repair order functionality.
Part of the InvenTree inventory management system.

This module provides comprehensive URL routing for repair order operations,
including CRUD, status management, parts/labor tracking, and export functionality.
"""

from __future__ import annotations

import logging
from typing import Final, List, Optional, Sequence, Set, Tuple, Type, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLPattern, URLResolver, include, path
from django.utils.translation import gettext_lazy as _
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.views import APIView

from . import api

# Module-level logger with structured logging support
logger = logging.getLogger(__name__)

# Constants for URL patterns
API_PREFIX: Final[str] = "api/order/"
REPAIR_ORDER_PREFIX: Final[str] = "repair-order/"
REPAIR_ORDER_PK: Final[str] = "repair-order/<int:pk>/"

# Required API view classes for validation
REQUIRED_API_VIEWS: Final[Tuple[str, ...]] = (
    "RepairOrderListCreateView",
    "RepairOrderDetailView",
    "RepairOrderCompleteView",
    "RepairOrderCancelView",
    "RepairOrderAddPartsView",
    "RepairOrderAddLaborView",
    "RepairOrderStatusView",
    "RepairOrderItemListView",
    "RepairOrderLaborListView",
    "RepairOrderExportView",
)

# URL pattern configuration with metadata
URL_PATTERN_CONFIG: Final[Tuple[Tuple[str, str, str], ...]] = (
    (REPAIR_ORDER_PREFIX, "RepairOrderListCreateView", "api-repair-order-list"),
    (REPAIR_ORDER_PK, "RepairOrderDetailView", "api-repair-order-detail"),
    (f"{REPAIR_ORDER_PK}complete/", "RepairOrderCompleteView", "api-repair-order-complete"),
    (f"{REPAIR_ORDER_PK}cancel/", "RepairOrderCancelView", "api-repair-order-cancel"),
    (f"{REPAIR_ORDER_PK}add-parts/", "RepairOrderAddPartsView", "api-repair-order-add-parts"),
    (f"{REPAIR_ORDER_PK}add-labor/", "RepairOrderAddLaborView", "api-repair-order-add-labor"),
    (f"{REPAIR_ORDER_PK}status/", "RepairOrderStatusView", "api-repair-order-status"),
    (f"{REPAIR_ORDER_PK}items/", "RepairOrderItemListView", "api-repair-order-items"),
    (f"{REPAIR_ORDER_PK}labor/", "RepairOrderLaborListView", "api-repair-order-labor"),
    (f"{REPAIR_ORDER_PK}export/", "RepairOrderExportView", "api-repair-order-export"),
)


class RepairOrderRouter:
    """
    Manages the creation and validation of repair order URL patterns.
    
    This class encapsulates all URL pattern generation logic for repair orders,
    providing centralized error handling, validation, and logging.
    
    Attributes:
        router: SimpleRouter instance for ViewSet-based endpoints
        _initialized: Flag indicating whether the router has been initialized
    """
    
    def __init__(self) -> None:
        """Initialize the RepairOrderRouter with default configuration."""
        self.router: SimpleRouter = DefaultRouter(trailing_slash=False)
        self._initialized: bool = False
        self._register_viewset()
    
    def _register_viewset(self) -> None:
        """
        Register the RepairOrderViewSet with the router.
        
        Raises:
            ImproperlyConfigured: If the viewset is not available in the api module
        """
        try:
            if not hasattr(api, "RepairOrderViewSet"):
                raise ImproperlyConfigured(
                    _("RepairOrderViewSet not found in order.api module")
                )
            
            self.router.register(
                prefix=REPAIR_ORDER_PREFIX.rstrip("/"),
                viewset=api.RepairOrderViewSet,
                basename="repair-order",
            )
            self._initialized = True
            
            logger.debug(
                "RepairOrderViewSet registered with router",
                extra={
                    "prefix": REPAIR_ORDER_PREFIX,
                    "basename": "repair-order",
                }
            )
            
        except ImproperlyConfigured as e:
            logger.error(
                "Failed to register RepairOrderViewSet: %s",
                str(e),
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error registering RepairOrderViewSet: %s",
                str(e),
                exc_info=True
            )
            raise ImproperlyConfigured(
                _("Failed to initialize repair order router")
            ) from e
    
    def validate_api_views(self) -> None:
        """
        Validate that all required API view classes exist in the api module.
        
        Raises:
            ImproperlyConfigured: If any required view class is missing
        """
        missing_views: List[str] = []
        
        for view_name in REQUIRED_API_VIEWS:
            if not hasattr(api, view_name):
                missing_views.append(view_name)
        
        if missing_views:
            error_msg = _("Missing required API views: {views}").format(
                views=", ".join(missing_views)
            )
            logger.error(
                "API view validation failed: %s",
                error_msg,
                extra={"missing_views": missing_views}
            )
            raise ImproperlyConfigured(error_msg)
        
        logger.debug(
            "All required API views validated successfully",
            extra={"view_count": len(REQUIRED_API_VIEWS)}
        )
    
    def create_url_patterns(self) -> List[URLPattern]:
        """
        Create and return repair order URL patterns.
        
        Returns:
            List of URLPattern objects for repair order endpoints
            
        Raises:
            ImproperlyConfigured: If URL pattern creation fails
        """
        try:
            self.validate_api_views()
            
            urls: List[URLPattern] = []
            
            for pattern, view_name, url_name in URL_PATTERN_CONFIG:
                try:
                    view_class: Type[APIView] = getattr(api, view_name)
                    url_pattern: URLPattern = path(
                        pattern,
                        view_class.as_view(),
                        name=url_name,
                    )
                    urls.append(url_pattern)
                    
                    logger.debug(
                        "Created URL pattern: %s -> %s",
                        url_name,
                        pattern,
                        extra={"view_class": view_name}
                    )
                    
                except AttributeError as e:
                    logger.error(
                        "Failed to create URL pattern for %s: %s",
                        view_name,
                        str(e),
                        exc_info=True
                    )
                    raise ImproperlyConfigured(
                        _("Failed to create URL pattern for {view}").format(view=view_name)
                    ) from e
            
            logger.info(
                "Created %d repair order URL patterns",
                len(urls),
                extra={"pattern_count": len(urls)}
            )
            
            return urls
            
        except ImproperlyConfigured:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error creating URL patterns: %s",
                str(e),
                exc_info=True
            )
            raise ImproperlyConfigured(
                _("Failed to create repair order URL patterns")
            ) from e
    
    def validate_url_patterns(self, urls: Sequence[URLPattern]) -> bool:
        """
        Validate URL patterns for uniqueness and correctness.
        
        Args:
            urls: Sequence of URLPattern objects to validate
            
        Returns:
            True if validation passes
            
        Raises:
            ImproperlyConfigured: If validation fails critically
        """
        try:
            url_names: Set[str] = set()
            duplicate_names: List[str] = []
            
            for url_pattern in urls:
                if hasattr(url_pattern, "name") and url_pattern.name:
                    if url_pattern.name in url_names:
                        duplicate_names.append(url_pattern.name)
                        logger.warning(
                            "Duplicate URL name found: %s",
                            url_pattern.name,
                            extra={"url_name": url_pattern.name}
                        )
                    url_names.add(url_pattern.name)
            
            if duplicate_names:
                logger.warning(
                    "Found %d duplicate URL names: %s",
                    len(duplicate_names),
                    ", ".join(duplicate_names),
                    extra={"duplicate_names": duplicate_names}
                )
            
            logger.debug(
                "Validated %d URL patterns with %d unique names",
                len(urls),
                len(url_names),
                extra={
                    "total_patterns": len(urls),
                    "unique_names": len(url_names),
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "URL pattern validation failed: %s",
                str(e),
                exc_info=True
            )
            raise ImproperlyConfigured(
                _("URL pattern validation failed")
            ) from e
    
    def get_combined_urlpatterns(self) -> List[URLPattern]:
        """
        Get combined repair order URL patterns from manual and router sources.
        
        Returns:
            Combined list of manually defined and router-generated URL patterns
            
        Raises:
            ImproperlyConfigured: If URL pattern generation fails
        """
        try:
            # Create manually defined URLs
            manual_urls: List[URLPattern] = self.create_url_patterns()
            
            # Get router URLs
            router_urls: List[URLPattern] = list(self.router.urls)
            
            # Combine all patterns
            combined_urls: List[URLPattern] = manual_urls + router_urls
            
            # Validate the combined patterns
            self.validate_url_patterns(combined_urls)
            
            logger.info(
                "Generated %d total repair order URL patterns (%d manual, %d router)",
                len(combined_urls),
                len(manual_urls),
                len(router_urls),
                extra={
                    "total": len(combined_urls),
                    "manual": len(manual_urls),
                    "router": len(router_urls),
                }
            )
            
            return combined_urls
            
        except ImproperlyConfigured:
            raise
        except Exception as e:
            logger.error(
                "Failed to generate combined URL patterns: %s",
                str(e),
                exc_info=True
            )
            raise ImproperlyConfigured(
                _("Failed to generate repair order URL patterns")
            ) from e


# Initialize the repair order router
try:
    repair_order_router_instance: RepairOrderRouter = RepairOrderRouter()
    repair_order_urlpatterns: List[URLPattern] = repair_order_router_instance.get_combined_urlpatterns()
    
    logger.info(
        "Repair order URL patterns initialized successfully",
        extra={"pattern_count": len(repair_order_urlpatterns)}
    )
    
except ImproperlyConfigured as e:
    logger.critical(
        "Failed to initialize repair order URLs: %s",
        str(e),
        exc_info=True
    )
    repair_order_urlpatterns = []
except Exception as e:
    logger.critical(
        "Unexpected error initializing repair order URLs: %s",
        str(e),
        exc_info=True
    )
    repair_order_urlpatterns = []

# Main URL patterns for the order app
urlpatterns: List[Union[URLPattern, URLResolver]] = [
    # Include existing order URLs (purchase orders, sales orders, etc.)
    path("", include("order.urls_base")),
]

# Only add repair order URLs if they were successfully generated
if repair_order_urlpatterns:
    try:
        urlpatterns.extend([
            # Include repair order URLs
            path(API_PREFIX, include(repair_order_urlpatterns)),
            
            # Include router URLs for repair orders
            path(API_PREFIX, include(repair_order_router_instance.router.urls)),
        ])
        
        logger.info(
            "Registered %d repair order URL patterns",
            len(repair_order_urlpatterns),
            extra={
                "api_prefix": API_PREFIX,
                "pattern_count": len(repair_order_urlpatterns),
            }
        )
    except Exception as e:
        logger.error(
            "Failed to register repair order URL patterns: %s",
            str(e),
            exc_info=True
        )
else:
    logger.warning(
        "No repair order URL patterns registered - repair order functionality disabled"
    )

# Export for use in other modules
__all__: Sequence[str] = [
    "urlpatterns",
    "repair_order_urlpatterns",
    "repair_order_router_instance",
    "RepairOrderRouter",
]

# Performance optimization: Pre-compile regex patterns if needed
if settings.DEBUG:
    logger.debug(
        "Running in DEBUG mode - URL patterns may be less performant",
        extra={"debug_mode": True}
    )