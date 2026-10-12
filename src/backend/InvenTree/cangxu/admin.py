"""Admin registrations for Cangxu records."""

from django.contrib import admin

from .models import (
    ComponentReplacement,
    ConfigurationItem,
    ConfigurationTestEvidence,
    CountLine,
    CountSession,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    MaterialIssue,
    MaterialReturn,
    PartCodeAlias,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
    ShipmentReceipt,
    ShipmentReceiptException,
    ShipmentReceiptLine,
    UnitConfiguration,
)


class CangxuReadOnlyAdmin(admin.ModelAdmin):
    """Keep workflow changes behind the audited Cangxu API actions."""

    def has_add_permission(self, request):
        """Prevent creating records without their workflow operation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent bypassing state transitions and inventory movements."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Preserve records that form part of a traceability history."""
        return False


admin.site.register(PartCodeAlias, CangxuReadOnlyAdmin)
admin.site.register(ManufacturingLot, CangxuReadOnlyAdmin)
admin.site.register(ManufacturingLotPartner, CangxuReadOnlyAdmin)
admin.site.register(ManufacturingLotStockItem, CangxuReadOnlyAdmin)
admin.site.register(MaterialIssue, CangxuReadOnlyAdmin)
admin.site.register(MaterialReturn, CangxuReadOnlyAdmin)
admin.site.register(UnitConfiguration, CangxuReadOnlyAdmin)
admin.site.register(ConfigurationItem, CangxuReadOnlyAdmin)
admin.site.register(ConfigurationTestEvidence, CangxuReadOnlyAdmin)
admin.site.register(ComponentReplacement, CangxuReadOnlyAdmin)
admin.site.register(QualityIssue, CangxuReadOnlyAdmin)
admin.site.register(ReworkTask, CangxuReadOnlyAdmin)
admin.site.register(ServiceCase, CangxuReadOnlyAdmin)
admin.site.register(ServiceCaseLine, CangxuReadOnlyAdmin)
admin.site.register(ServiceCaseEvent, CangxuReadOnlyAdmin)
admin.site.register(CountSession, CangxuReadOnlyAdmin)
admin.site.register(CountLine, CangxuReadOnlyAdmin)
admin.site.register(ShipmentManifest, CangxuReadOnlyAdmin)
admin.site.register(ShipmentManifestLine, CangxuReadOnlyAdmin)
admin.site.register(ShipmentReceipt, CangxuReadOnlyAdmin)
admin.site.register(ShipmentReceiptLine, CangxuReadOnlyAdmin)
admin.site.register(ShipmentReceiptException, CangxuReadOnlyAdmin)
