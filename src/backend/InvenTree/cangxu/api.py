"""REST API for Cangxu manufacturing and service traceability."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Max, Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

import InvenTree.permissions
from order.models import SalesOrderShipment
from part.models import Part
from plugin.base.event.events import batch_events
from stock.models import StockItem, batch_tracking_entries
from stock.status_codes import StockHistoryCode, StockStatus, StockStatusGroups

from . import serializers
from .importers import (
    WorkbookImportError,
    normalize_workbook_rows,
    parse_workbook_rows,
    validate_normalized_import_values,
)
from .models import (
    CableEndDefinition,
    ComponentReplacement,
    ConfigurationItem,
    ConfigurationTestEvidence,
    CountLine,
    CountSession,
    DataImportBatch,
    DataImportRecord,
    HardwarePortDefinition,
    HardwareProfileRevision,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    PartCodeAlias,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
    UnitConfiguration,
)


class CangxuModelViewSet(viewsets.ModelViewSet):
    """Use the standard InvenTree role rules for every industry resource."""

    permission_classes = [InvenTree.permissions.RolePermissionOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']


class PartCodeAliasViewSet(CangxuModelViewSet):
    """Look up ERP and vendor codes without duplicating Part records."""

    queryset = PartCodeAlias.objects.select_related('part', 'company')
    serializer_class = serializers.PartCodeAliasSerializer
    filterset_fields = ['part', 'namespace', 'source_system', 'company']
    search_fields = ['code', 'normalized_code', 'source_system']
    ordering_fields = ['namespace', 'code', 'created']
    ordering = ['namespace', 'normalized_code']


class HardwareProfileRevisionViewSet(CangxuModelViewSet):
    """Manage engineering specifications independently from stock and vendors."""

    role_required = 'part'
    queryset = HardwareProfileRevision.objects.select_related(
        'part', 'chip_vendor', 'board_manufacturer', 'created_by', 'approved_by'
    ).prefetch_related('ports', 'cable_ends')
    serializer_class = serializers.HardwareProfileRevisionSerializer
    filterset_fields = ['part', 'kind', 'protocol', 'form_factor', 'state']
    search_fields = ['part__name', 'part__IPN', 'revision', 'source_reference']
    ordering_fields = ['part', 'revision', 'kind', 'protocol', 'created_at']
    ordering = ['part', '-created_at']

    def perform_create(self, serializer):
        """Attribute a draft profile to the engineering user creating it."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Keep approved hardware revisions immutable."""
        if serializer.instance.state != HardwareProfileRevision.State.DRAFT:
            raise ValidationError(
                _('Create a new revision to change an approved profile.')
            )
        serializer.save()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        """Approve sourced specifications and supersede the previous active revision."""
        profile = HardwareProfileRevision.objects.select_for_update().get(
            pk=self.get_object().pk
        )
        if profile.state != HardwareProfileRevision.State.DRAFT:
            raise ValidationError(_('Only draft hardware profiles can be approved.'))
        if not profile.source_reference.strip():
            raise ValidationError({
                'source_reference': _('Record the approved engineering source first.')
            })

        switch_kinds = {
            HardwareProfileRevision.Kind.PCIE_SWITCH,
            HardwareProfileRevision.Kind.NVLINK_SWITCH,
            HardwareProfileRevision.Kind.ETHERNET_SWITCH,
            HardwareProfileRevision.Kind.INFINIBAND_SWITCH,
        }
        if profile.kind in switch_kinds and not profile.ports.exists():
            raise ValidationError(_('Add at least one typed port before approval.'))
        if (
            profile.kind
            in {
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Kind.POWER_HARNESS,
            }
            and profile.cable_ends.count() < 2
        ):
            raise ValidationError(_('Define at least two cable ends before approval.'))

        previous = (
            HardwareProfileRevision.objects
            .select_for_update()
            .filter(part=profile.part, state=HardwareProfileRevision.State.APPROVED)
            .exclude(pk=profile.pk)
            .first()
        )
        if previous:
            previous.state = HardwareProfileRevision.State.SUPERSEDED
            previous.save(update_fields=['state'])
            profile.supersedes = previous

        profile.state = HardwareProfileRevision.State.APPROVED
        profile.approved_by = request.user
        profile.approved_at = timezone.now()
        profile.save(
            update_fields=['state', 'approved_by', 'approved_at', 'supersedes']
        )
        return Response(self.get_serializer(profile).data)


class HardwarePortDefinitionViewSet(CangxuModelViewSet):
    """Manage protocol-specific ports on draft hardware profiles."""

    role_required = 'part'
    queryset = HardwarePortDefinition.objects.select_related('profile', 'profile__part')
    serializer_class = serializers.HardwarePortDefinitionSerializer
    filterset_fields = ['profile', 'protocol']
    search_fields = ['path', 'connector', 'profile__part__IPN']
    ordering_fields = ['profile', 'path', 'protocol']
    ordering = ['profile', 'path']

    def _require_draft_profile(self, profile):
        """Prevent edits to ports after the engineering revision is approved."""
        if profile.state != HardwareProfileRevision.State.DRAFT:
            raise ValidationError(_('Ports can only change on a draft profile.'))

    def perform_create(self, serializer):
        """Create a port only beneath an editable revision."""
        self._require_draft_profile(serializer.validated_data['profile'])
        serializer.save()

    def perform_update(self, serializer):
        """Update a port only while its current parent revision is a draft."""
        self._require_draft_profile(serializer.instance.profile)
        profile = serializer.validated_data.get('profile', serializer.instance.profile)
        self._require_draft_profile(profile)
        serializer.save()


class CableEndDefinitionViewSet(CangxuModelViewSet):
    """Manage two-ended and multi-branch cable specifications."""

    role_required = 'part'
    queryset = CableEndDefinition.objects.select_related('profile', 'profile__part')
    serializer_class = serializers.CableEndDefinitionSerializer
    filterset_fields = ['profile', 'protocol', 'branch_group']
    search_fields = ['label', 'connector', 'profile__part__IPN']
    ordering_fields = ['profile', 'label', 'protocol']
    ordering = ['profile', 'label']

    def _validate_profile(self, profile, protocol):
        """Ensure an end belongs to a cable profile and matches its declared protocol."""
        if profile.state != HardwareProfileRevision.State.DRAFT:
            raise ValidationError(_('Cable ends can only change on a draft profile.'))
        if profile.kind not in {
            HardwareProfileRevision.Kind.CABLE,
            HardwareProfileRevision.Kind.POWER_HARNESS,
        }:
            raise ValidationError(
                _('Cable ends require a cable or power harness profile.')
            )
        if profile.protocol != protocol:
            raise ValidationError(_('Cable end protocol must match its profile.'))

    def perform_create(self, serializer):
        """Create an end only beneath a draft cable profile."""
        self._validate_profile(
            serializer.validated_data['profile'], serializer.validated_data['protocol']
        )
        serializer.save()

    def perform_update(self, serializer):
        """Update an end only while both old and new parent profiles are drafts."""
        current = serializer.instance
        profile = serializer.validated_data.get('profile', current.profile)
        protocol = serializer.validated_data.get('protocol', current.protocol)
        self._validate_profile(current.profile, current.protocol)
        self._validate_profile(profile, protocol)
        serializer.save()


class ManufacturingLotViewSet(CangxuModelViewSet):
    """Trace a part batch and the suppliers or manufacturing partners behind it."""

    queryset = ManufacturingLot.objects.select_related(
        'part', 'purchase_order_line', 'purchase_order_line__part'
    ).prefetch_related('partners', 'stock_items')
    serializer_class = serializers.ManufacturingLotSerializer
    filterset_fields = ['part', 'code', 'production_date', 'purchase_order_line']
    search_fields = ['code', 'part__name', 'part__IPN']
    ordering_fields = ['code', 'production_date', 'created']
    ordering = ['-created']


class ManufacturingLotPartnerViewSet(CangxuModelViewSet):
    """Record the distinct board, PCB, SMT, OEM, and supplier roles."""

    queryset = ManufacturingLotPartner.objects.select_related('lot', 'company')
    serializer_class = serializers.ManufacturingLotPartnerSerializer
    filterset_fields = ['lot', 'company', 'role']
    ordering_fields = ['role', 'id']


class ManufacturingLotStockItemViewSet(CangxuModelViewSet):
    """Associate received or assembled stock with its source batch."""

    queryset = ManufacturingLotStockItem.objects.select_related(
        'lot', 'stock_item', 'stock_item__part'
    )
    serializer_class = serializers.ManufacturingLotStockItemSerializer
    filterset_fields = ['lot', 'stock_item']


class UnitConfigurationViewSet(CangxuModelViewSet):
    """Create consecutive configuration revisions and release verified snapshots."""

    queryset = UnitConfiguration.objects.select_related(
        'unit', 'unit__part', 'created_by', 'supersedes'
    ).prefetch_related('items__component', 'test_evidence__test_result')
    serializer_class = serializers.UnitConfigurationSerializer
    filterset_fields = ['unit', 'state', 'kind']
    search_fields = ['unit__serial', 'unit__part__name', 'change_summary']
    ordering_fields = ['revision', 'created', 'released_at']
    ordering = ['unit', '-revision']

    @transaction.atomic
    def perform_create(self, serializer):
        """Lock the unit, allocate a revision, and copy the last actual fit."""
        unit_id = serializer.validated_data['unit'].pk
        try:
            unit = (
                StockItem.objects
                .select_for_update()
                .select_related('part')
                .get(pk=unit_id)
            )
        except StockItem.DoesNotExist as exc:
            raise ValidationError({
                'unit': _('The stock item does not exist.')
            }) from exc

        previous = (
            UnitConfiguration.objects
            .select_for_update()
            .filter(unit=unit)
            .order_by('-revision')
            .first()
        )
        if previous and previous.state == UnitConfiguration.State.DRAFT:
            raise ValidationError({
                'unit': _(
                    'Finish or discard the existing draft before creating a revision.'
                )
            })

        revision = (previous.revision if previous else 0) + 1
        config = serializer.save(
            unit=unit,
            revision=revision,
            created_by=self.request.user,
            supersedes=previous,
        )

        if previous:
            ConfigurationItem.objects.bulk_create([
                ConfigurationItem(
                    configuration=config,
                    component=item.component,
                    position=item.position,
                    quantity=item.quantity,
                    installed_at=item.installed_at,
                    installed_by=item.installed_by,
                    source_build_line=item.source_build_line,
                    source_build_item=item.source_build_item,
                )
                for item in previous.items.filter(
                    removed_at__isnull=True
                ).select_related('component')
            ])

    def _required_subjects(self, configuration):
        """Return the unit and current installed components whose tests apply."""
        subjects = [configuration.unit]
        subjects.extend(
            item.component
            for item in configuration.items.filter(
                removed_at__isnull=True
            ).select_related('component', 'component__part')
        )
        return subjects

    def _missing_configuration_tests(self, configuration):
        """Find required Part tests without passing evidence for this revision."""
        missing = []
        for subject in self._required_subjects(configuration):
            for template in subject.part.getRequiredTests():
                passed = ConfigurationTestEvidence.objects.filter(
                    configuration=configuration,
                    test_result__stock_item=subject,
                    test_result__template=template,
                    test_result__result=True,
                    test_result__date__gte=configuration.created,
                ).exists()
                if not passed:
                    missing.append(f'{subject.pk}:{template.test_name}')
        return missing

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def release(self, request, pk=None):
        """Release only a completed unit with current-version test evidence."""
        configuration_id = self.get_object().pk
        unit_id = UnitConfiguration.objects.values_list('unit_id', flat=True).get(
            pk=configuration_id
        )
        unit = StockItem.objects.select_for_update().get(pk=unit_id)
        configuration = UnitConfiguration.objects.select_for_update().get(
            pk=configuration_id
        )
        if configuration.state != UnitConfiguration.State.DRAFT:
            raise ValidationError(_('Only a draft configuration can be released.'))

        if unit.is_building:
            raise ValidationError(_('The unit build must be completed before release.'))

        blocking_issues = QualityIssue.objects.filter(
            Q(unit=unit) | Q(component__in=configuration.items.values('component_id')),
            severity=QualityIssue.Severity.BLOCKER,
        ).exclude(state=QualityIssue.State.CLOSED)
        if blocking_issues.exists():
            raise ValidationError({
                'quality': _('Open blocking quality issues prevent release.')
            })

        missing_tests = self._missing_configuration_tests(configuration)
        if missing_tests:
            raise ValidationError({
                'tests': _(
                    'Required tests are missing or failed for this configuration.'
                ),
                'missing': missing_tests,
            })

        active_items = configuration.items.filter(
            removed_at__isnull=True
        ).select_related('component', 'component__part')
        snapshot = {
            'unit': {
                'stock_item': unit.pk,
                'part': unit.part_id,
                'part_name': unit.part.name,
                'serial': unit.serial,
                'batch': unit.batch,
            },
            'revision': configuration.revision,
            'kind': configuration.kind,
            'firmware': configuration.firmware,
            'items': [
                {
                    'stock_item': item.component_id,
                    'part': item.component.part_id,
                    'part_name': item.component.part.name,
                    'serial': item.component.serial,
                    'batch': item.component.batch,
                    'position': item.position,
                    'quantity': str(item.quantity),
                    'installed_at': item.installed_at.isoformat(),
                }
                for item in active_items
            ],
        }
        configuration.bom_snapshot = snapshot
        configuration.state = UnitConfiguration.State.RELEASED
        configuration.released_at = timezone.now()
        configuration.save(update_fields=['bom_snapshot', 'state', 'released_at'])
        if configuration.supersedes:
            UnitConfiguration.objects.filter(
                pk=configuration.supersedes_id, state=UnitConfiguration.State.RELEASED
            ).update(state=UnitConfiguration.State.SUPERSEDED)

        return Response(self.get_serializer(configuration).data)


class ConfigurationItemViewSet(CangxuModelViewSet):
    """Manage installed components through InvenTree's stock operations."""

    queryset = ConfigurationItem.objects.select_related(
        'configuration__unit', 'component', 'component__part', 'installed_by'
    )
    serializer_class = serializers.ConfigurationItemSerializer
    filterset_fields = ['configuration', 'component', 'position', 'removed_at']
    ordering_fields = ['position', 'installed_at', 'removed_at']
    ordering = ['configuration', 'position']

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def replace(self, request, pk=None):
        """Atomically remove one component and install its like-for-like replacement."""
        item_id = self.get_object().pk
        configuration_id, unit_id = ConfigurationItem.objects.values_list(
            'configuration_id', 'configuration__unit_id'
        ).get(pk=item_id)
        unit = StockItem.objects.select_for_update().get(pk=unit_id)
        config = UnitConfiguration.objects.select_for_update().get(pk=configuration_id)
        item = (
            ConfigurationItem.objects
            .select_for_update()
            .select_related('configuration', 'component')
            .get(pk=item_id)
        )
        if config.state != UnitConfiguration.State.DRAFT:
            raise ValidationError(
                _('Create a draft configuration before replacing components.')
            )
        if config.test_evidence.exists():
            raise ValidationError(
                _('Create a new configuration revision after testing.')
            )
        if item.removed_at:
            raise ValidationError(
                _('This configured component has already been removed.')
            )

        action_data = serializers.ComponentReplacementRequestSerializer(
            data=request.data
        )
        action_data.is_valid(raise_exception=True)
        replacement = (
            StockItem.objects
            .select_for_update()
            .select_related('part', 'location')
            .get(pk=action_data.validated_data['replacement_item'].pk)
        )
        previous = (
            StockItem.objects
            .select_for_update()
            .select_related('part')
            .get(pk=item.component_id)
        )
        destination = action_data.validated_data['destination_location']
        reason = action_data.validated_data['reason'].strip()
        rework_task = action_data.validated_data.get('rework_task')

        if rework_task:
            rework_task = (
                ReworkTask.objects
                .select_for_update()
                .select_related('issue')
                .get(pk=rework_task.pk)
            )
            if (
                rework_task.issue.unit_id != unit.pk
                or (
                    rework_task.issue.component_id
                    and rework_task.issue.component_id != previous.pk
                )
                or rework_task.issue.state != QualityIssue.State.REWORK
                or rework_task.state != ReworkTask.State.IN_PROGRESS
            ):
                raise ValidationError({
                    'rework_task': _(
                        'The rework task must be in progress for this unit and quality issue.'
                    )
                })

        if not reason:
            raise ValidationError({'reason': _('A replacement reason is required.')})
        if previous.belongs_to_id != unit.pk:
            raise ValidationError(
                _('The previous component is no longer installed in this unit.')
            )
        if replacement.part_id != previous.part_id:
            raise ValidationError(
                _(
                    'A replacement must use the same part until an approved substitute is linked.'
                )
            )
        if not destination or destination.structural or destination.external:
            raise ValidationError({
                'destination_location': _(
                    'Choose an internal, non-structural location.'
                )
            })
        if not replacement.location or replacement.location.external:
            raise ValidationError(
                _('The replacement must be in an internal stock location.')
            )
        if (
            not replacement.is_in_stock()
            or replacement.status not in StockStatusGroups.AVAILABLE_CODES
        ):
            raise ValidationError(
                _('The replacement item is not available for installation.')
            )
        if replacement.allocation_count() > 0:
            raise ValidationError(_('Allocated stock cannot be installed.'))
        if replacement.quantity < previous.quantity:
            raise ValidationError(_('Insufficient replacement quantity.'))
        if replacement.serialized and previous.quantity != 1:
            raise ValidationError(_('Serialized replacement quantity must be one.'))

        user = request.user
        now = timezone.now()
        try:
            previous.uninstall_into_location(destination, user, notes=reason)
            installed_item = replacement
            if previous.quantity < replacement.quantity:
                installed_item = replacement.splitStock(
                    previous.quantity, replacement.location, user, notes=reason
                )
                if installed_item is None:
                    raise ValidationError(
                        _('The replacement stock could not be split.')
                    )
            unit.installStockItem(
                installed_item,
                previous.quantity,
                user,
                notes=f'Cangxu replacement at {item.position}: {reason}',
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            ) from exc

        item.removed_at = now
        item.removed_by = user
        item.removal_reason = reason
        item.save(update_fields=['removed_at', 'removed_by', 'removal_reason'])
        next_item = ConfigurationItem.objects.create(
            configuration=config,
            component=installed_item,
            position=item.position,
            quantity=item.quantity,
            installed_by=user,
            source_build_item=item.source_build_item,
        )
        replacement_record = ComponentReplacement.objects.create(
            unit=unit,
            configuration=config,
            previous_configuration=item.configuration,
            previous_item=previous,
            replacement_item=installed_item,
            position=item.position,
            reason=reason,
            changed_by=user,
            rework_task=rework_task,
        )
        return Response({
            'removed': self.get_serializer(item).data,
            'installed': self.get_serializer(next_item).data,
            'replacement': serializers.ComponentReplacementSerializer(
                replacement_record
            ).data,
        })

    @transaction.atomic
    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        config = UnitConfiguration.objects.select_for_update().get(
            pk=serializer.validated_data['configuration'].pk
        )
        if config.state != UnitConfiguration.State.DRAFT:
            raise ValidationError(_('Only a draft configuration can be changed.'))
        if config.test_evidence.exists():
            raise ValidationError(
                _('Create a new configuration revision after recording test evidence.')
            )

        component = (
            StockItem.objects
            .select_for_update()
            .select_related('part')
            .get(pk=serializer.validated_data['component'].pk)
        )
        if component.belongs_to_id == config.unit_id:
            # Native Build completion may already have installed this component.
            # In that case record its engineering position without moving stock again.
            source_build_line = serializer.validated_data.get('source_build_line')
            if (
                component.consumed_by_id == config.unit.build_id
                and component.consumed_by_id
            ):
                build_lines = config.unit.build.build_lines.filter(
                    bom_item__sub_part_id=component.part_id
                )
                if source_build_line:
                    if not build_lines.filter(pk=source_build_line.pk).exists():
                        raise ValidationError({
                            'source_build_line': _(
                                'The work order line does not allocate this component to the unit.'
                            )
                        })
                else:
                    matching_lines = list(build_lines[:2])
                    if len(matching_lines) > 1:
                        raise ValidationError({
                            'source_build_line': _(
                                'Select the exact work order line for this component.'
                            )
                        })
                    if matching_lines:
                        source_build_line = matching_lines[0]
            serializer.save(
                component=component,
                installed_by=self.request.user,
                source_build_line=source_build_line,
            )
            return
        quantity = Decimal(serializer.validated_data.get('quantity', 1))
        if component.belongs_to_id or component.sales_order_id is not None:
            raise ValidationError({
                'component': _(
                    'The component is already installed or assigned to an order.'
                )
            })
        if component.allocation_count() > 0:
            raise ValidationError({
                'component': _('Allocated stock cannot be installed.')
            })
        if quantity > component.quantity:
            raise ValidationError({'quantity': _('Quantity exceeds available stock.')})

        install_item = component
        if quantity < component.quantity:
            install_item = component.splitStock(quantity, user=request_user(self))
            if install_item is None:
                raise ValidationError({
                    'quantity': _('The stock item could not be split.')
                })

        try:
            config.unit.installStockItem(
                install_item,
                quantity,
                self.request.user,
                notes=f'Cangxu configuration R{config.revision}: {serializer.validated_data["position"]}',
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            ) from exc

        serializer.save(component=install_item, installed_by=self.request.user)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def remove(self, request, pk=None):
        """Remove an installed component and return it to a real stock location."""
        item = self.get_object()
        config = UnitConfiguration.objects.select_for_update().get(
            pk=item.configuration_id
        )
        item = ConfigurationItem.objects.select_for_update().get(pk=item.pk)
        if config.state != UnitConfiguration.State.DRAFT:
            raise ValidationError(
                _('Create a new configuration revision before removing items.')
            )
        if config.test_evidence.exists():
            raise ValidationError(
                _('Create a new configuration revision after testing.')
            )
        if item.removed_at:
            raise ValidationError(_('This component has already been removed.'))

        removal = serializers.ComponentRemovalRequestSerializer(data=request.data)
        removal.is_valid(raise_exception=True)
        destination = removal.validated_data['location']
        reason = removal.validated_data['reason']
        removal_kind = removal.validated_data['removal_kind']
        if destination.structural or destination.external:
            raise ValidationError({
                'location': _('Choose an internal, non-structural location.')
            })

        component = StockItem.objects.select_for_update().get(pk=item.component_id)
        if component.belongs_to_id != config.unit_id:
            raise ValidationError(
                _('The component is no longer installed in this unit.')
            )
        try:
            component.uninstall_into_location(
                destination, request.user, notes=f'{removal_kind}: {reason}'
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            ) from exc

        item.removed_at = timezone.now()
        item.removed_by = request.user
        item.removal_reason = reason
        item.removal_kind = removal_kind
        item.save(
            update_fields=['removed_at', 'removed_by', 'removal_reason', 'removal_kind']
        )
        return Response(self.get_serializer(item).data)


def request_user(view):
    """Return the authenticated user for model operations."""
    return view.request.user


class ConfigurationTestEvidenceViewSet(CangxuModelViewSet):
    """Attach native test results to the exact configuration revision they validate."""

    queryset = ConfigurationTestEvidence.objects.select_related(
        'configuration',
        'test_result',
        'test_result__stock_item',
        'test_result__template',
    )
    serializer_class = serializers.ConfigurationTestEvidenceSerializer
    filterset_fields = ['configuration', 'test_result']
    http_method_names = ['get', 'post', 'head', 'options']

    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        config = serializer.validated_data['configuration']
        result = serializer.validated_data['test_result']
        if config.state != UnitConfiguration.State.DRAFT:
            raise ValidationError(_('Test evidence can only be added to a draft.'))
        if not result.result:
            raise ValidationError(
                _('Only a passing result can satisfy release evidence.')
            )

        valid_subject_ids = {config.unit_id}
        valid_subject_ids.update(
            config.items.filter(removed_at__isnull=True).values_list(
                'component_id', flat=True
            )
        )
        if result.stock_item_id not in valid_subject_ids:
            raise ValidationError({
                'test_result': _(
                    'The test result does not belong to this configuration.'
                )
            })

        latest_installation = config.items.filter(
            component_id=result.stock_item_id, removed_at__isnull=True
        ).aggregate(latest=Max('installed_at'))['latest']
        result_time = result.finished_datetime or result.date
        if result_time < config.created or (
            latest_installation and result_time < latest_installation
        ):
            raise ValidationError({
                'test_result': _('The test result predates this configuration change.')
            })
        serializer.save(recorded_by=self.request.user)


class ComponentReplacementViewSet(CangxuModelViewSet):
    """Expose immutable component replacement history."""

    queryset = ComponentReplacement.objects.select_related(
        'unit',
        'configuration',
        'previous_configuration',
        'previous_item',
        'replacement_item',
        'changed_by',
    )
    serializer_class = serializers.ComponentReplacementSerializer
    filterset_fields = ['unit', 'configuration', 'previous_item', 'replacement_item']
    ordering_fields = ['changed_at', 'position']
    ordering = ['-changed_at']
    http_method_names = ['get', 'head', 'options']


class QualityIssueViewSet(CangxuModelViewSet):
    """Manage quality issues with explicit state transitions."""

    queryset = QualityIssue.objects.select_related(
        'unit', 'component', 'detected_by', 'closed_by'
    ).prefetch_related('rework_tasks')
    serializer_class = serializers.QualityIssueSerializer
    filterset_fields = ['reference', 'unit', 'component', 'severity', 'state']
    search_fields = ['reference', 'title', 'description']
    ordering_fields = ['detected_at', 'severity', 'state']
    ordering = ['-detected_at']

    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        serializer.save(detected_by=self.request.user)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def transition(self, request, pk=None):
        """Move the record to an allowed workflow state."""
        issue = QualityIssue.objects.select_for_update().get(pk=self.get_object().pk)
        action_data = serializers.StateTransitionSerializer(data=request.data)
        action_data.is_valid(raise_exception=True)
        target = action_data.validated_data['state']
        transitions = {
            QualityIssue.State.OPEN: {QualityIssue.State.INVESTIGATING},
            QualityIssue.State.INVESTIGATING: {QualityIssue.State.REWORK},
            QualityIssue.State.REWORK: {QualityIssue.State.VERIFY},
            QualityIssue.State.VERIFY: {QualityIssue.State.INVESTIGATING},
        }
        if target not in transitions.get(issue.state, set()):
            raise ValidationError(_('This quality issue transition is not allowed.'))
        issue.state = target
        issue.save(update_fields=['state'])
        return Response(self.get_serializer(issue).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def close(self, request, pk=None):
        """Validate outstanding work and close the record."""
        issue = QualityIssue.objects.select_for_update().get(pk=self.get_object().pk)
        note = str(request.data.get('verification_notes', '')).strip()
        if issue.state != QualityIssue.State.VERIFY:
            raise ValidationError(
                _('The issue must be awaiting verification before closure.')
            )
        if not note:
            raise ValidationError({
                'verification_notes': _('Verification evidence is required.')
            })
        if issue.rework_tasks.exclude(state=ReworkTask.State.COMPLETE).exists():
            raise ValidationError(_('All related rework tasks must be verified first.'))
        issue.verification_notes = note
        issue.state = QualityIssue.State.CLOSED
        issue.closed_at = timezone.now()
        issue.closed_by = request.user
        issue.save(
            update_fields=['verification_notes', 'state', 'closed_at', 'closed_by']
        )
        return Response(self.get_serializer(issue).data)


class ReworkTaskViewSet(CangxuModelViewSet):
    """Manage corrective work and require recorded verification to finish."""

    queryset = ReworkTask.objects.select_related('issue', 'assigned_to', 'verified_by')
    serializer_class = serializers.ReworkTaskSerializer
    filterset_fields = ['issue', 'state', 'assigned_to']
    search_fields = ['title', 'instructions', 'issue__reference']
    ordering_fields = ['created', 'state']
    ordering = ['state', '-created']

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def transition(self, request, pk=None):
        """Move the record to an allowed workflow state."""
        task = self.get_object()
        action_data = serializers.StateTransitionSerializer(data=request.data)
        action_data.is_valid(raise_exception=True)
        target = action_data.validated_data['state']
        transitions = {
            ReworkTask.State.OPEN: {ReworkTask.State.IN_PROGRESS},
            ReworkTask.State.IN_PROGRESS: {ReworkTask.State.VERIFY},
        }
        if target not in transitions.get(task.state, set()):
            raise ValidationError(_('This rework task transition is not allowed.'))
        if target == ReworkTask.State.VERIFY and not action_data.validated_data.get(
            'note'
        ):
            raise ValidationError({'note': _('Work completion notes are required.')})
        task.state = target
        if target == ReworkTask.State.VERIFY:
            task.verification_notes = action_data.validated_data['note']
        task.save(update_fields=['state', 'verification_notes'])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def verify(self, request, pk=None):
        """Record independent verification and complete the task."""
        task = self.get_object()
        note = str(request.data.get('note', '')).strip()
        if task.state != ReworkTask.State.VERIFY:
            raise ValidationError(_('The rework task is not awaiting verification.'))
        if not note:
            raise ValidationError({'note': _('Verification notes are required.')})
        task.state = ReworkTask.State.COMPLETE
        task.verified_by = request.user
        task.verification_notes = f'{task.verification_notes}\n{note}'.strip()
        task.completed_at = timezone.now()
        task.save(
            update_fields=['state', 'verified_by', 'verification_notes', 'completed_at']
        )
        return Response(self.get_serializer(task).data)


class ServiceCaseViewSet(CangxuModelViewSet):
    """Manage customer return and supplier repair cases separately."""

    queryset = ServiceCase.objects.select_related(
        'customer',
        'supplier',
        'source_shipment',
        'source_shipment__order',
        'unit',
        'opened_by',
        'closed_by',
    ).prefetch_related('lines__events')
    serializer_class = serializers.ServiceCaseSerializer
    filterset_fields = [
        'reference',
        'kind',
        'state',
        'customer',
        'supplier',
        'source_shipment',
        'unit',
    ]
    search_fields = ['reference', 'external_reference', 'description']
    ordering_fields = ['opened_at', 'state', 'kind']
    ordering = ['-opened_at']

    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        serializer.save(opened_by=self.request.user)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def close(self, request, pk=None):
        """Validate outstanding work and close the record."""
        case = ServiceCase.objects.select_for_update().get(pk=self.get_object().pk)
        if case.lines.filter(outcome=ServiceCaseLine.Outcome.PENDING).exists():
            raise ValidationError(
                _('Resolve every service line before closing the case.')
            )
        for line in case.lines.all():
            events = line.events.order_by('occurred_at', 'id')
            sent = events.filter(event_type=ServiceCaseEvent.EventType.SENT).aggregate(
                total=Sum('quantity')
            )['total'] or Decimal(0)
            returned = events.filter(
                event_type=ServiceCaseEvent.EventType.RETURNED
            ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
            disposed = events.filter(
                event_type=ServiceCaseEvent.EventType.DISPOSED
            ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
            scrapped = events.filter(
                event_type=ServiceCaseEvent.EventType.SCRAPPED
            ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
            inspected = events.filter(
                event_type=ServiceCaseEvent.EventType.INSPECTED
            ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
            received = events.filter(
                event_type__in=[
                    ServiceCaseEvent.EventType.RECEIVED,
                    ServiceCaseEvent.EventType.RETURNED,
                ]
            ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)

            if returned + disposed > sent:
                raise ValidationError(
                    _(
                        'Returned or disposed quantity exceeds the quantity sent for line %(line)s.'
                    )
                    % {'line': line.pk}
                )
            if scrapped > received:
                raise ValidationError(
                    _(
                        'Scrapped quantity exceeds the received quantity for line %(line)s.'
                    )
                    % {'line': line.pk}
                )
            if (
                sent > returned + disposed
                and line.outcome != ServiceCaseLine.Outcome.NOT_RETURNED
            ):
                raise ValidationError(
                    _('A supplier return is still outstanding for line %(line)s.')
                    % {'line': line.pk}
                )
            if line.outcome == ServiceCaseLine.Outcome.NOT_RETURNED and sent == 0:
                raise ValidationError(
                    _(
                        'A line cannot be marked not returned unless it was sent externally.'
                    )
                )
            if (
                line.outcome == ServiceCaseLine.Outcome.SCRAPPED
                and scrapped + disposed < line.quantity
            ):
                raise ValidationError(
                    _(
                        'Record the disposition of every scrapped quantity for line %(line)s.'
                    )
                    % {'line': line.pk}
                )
            if inspected < received:
                raise ValidationError(
                    _('Inspect every received quantity before closing line %(line)s.')
                    % {'line': line.pk}
                )
        case.state = ServiceCase.State.CLOSED
        case.closed_at = timezone.now()
        case.closed_by = request.user
        case.save(update_fields=['state', 'closed_at', 'closed_by'])
        return Response(self.get_serializer(case).data)


class ServiceCaseLineViewSet(CangxuModelViewSet):
    """Resolve repair outcomes one item at a time."""

    queryset = ServiceCaseLine.objects.select_related(
        'case', 'stock_item', 'replacement_item'
    ).prefetch_related('events')
    serializer_class = serializers.ServiceCaseLineSerializer
    filterset_fields = ['case', 'stock_item', 'outcome']

    @transaction.atomic
    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        case = ServiceCase.objects.select_for_update().get(
            pk=serializer.validated_data['case'].pk
        )
        if case.state == ServiceCase.State.CLOSED:
            raise ValidationError(_('The service case is closed.'))
        serializer.save()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def resolve(self, request, pk=None):
        """Record the final outcome for this service line."""
        current = self.get_object()
        case = ServiceCase.objects.select_for_update().get(pk=current.case_id)
        line = (
            ServiceCaseLine.objects
            .select_for_update()
            .select_related('case', 'stock_item')
            .get(pk=current.pk)
        )
        action_data = serializers.ServiceResolutionSerializer(data=request.data)
        action_data.is_valid(raise_exception=True)
        if case.state == ServiceCase.State.CLOSED:
            raise ValidationError(_('The service case is closed.'))

        outcome = action_data.validated_data['outcome']
        replacement = action_data.validated_data.get('replacement_item')
        if outcome == ServiceCaseLine.Outcome.REPLACED:
            if replacement is None:
                raise ValidationError({
                    'replacement_item': _('A replacement item is required.')
                })
            if replacement.pk == line.stock_item_id:
                raise ValidationError(
                    _('The replacement must be a different stock item.')
                )
            if replacement.part_id != line.stock_item.part_id:
                raise ValidationError(
                    _('The replacement must match the returned part.')
                )
            replacement = (
                StockItem.objects
                .select_for_update()
                .select_related('location')
                .get(pk=replacement.pk)
            )
            if (
                not replacement.location
                or replacement.location.external
                or not replacement.is_in_stock()
                or replacement.allocation_count() > 0
            ):
                raise ValidationError({
                    'replacement_item': _(
                        'The replacement is not available in internal stock.'
                    )
                })
        elif replacement is not None:
            raise ValidationError({
                'replacement_item': _('Only replacements use this field.')
            })

        line.outcome = outcome
        line.replacement_item = replacement
        line.notes = action_data.validated_data.get('notes', '')
        line.save(update_fields=['outcome', 'replacement_item', 'notes'])
        return Response(self.get_serializer(line).data)


class ServiceCaseEventViewSet(CangxuModelViewSet):
    """Append and list custody events; events cannot be edited or deleted."""

    queryset = ServiceCaseEvent.objects.select_related(
        'line__case',
        'line__stock_item',
        'stock_item',
        'company',
        'from_location',
        'to_location',
        'created_by',
    )
    serializer_class = serializers.ServiceCaseEventSerializer
    filterset_fields = [
        'line',
        'stock_item',
        'event_type',
        'company',
        'from_location',
        'to_location',
    ]
    ordering_fields = ['occurred_at']
    ordering = ['occurred_at', 'id']
    http_method_names = ['get', 'post', 'head', 'options']

    @transaction.atomic
    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        candidate = serializer.validated_data['line']
        case = ServiceCase.objects.select_for_update().get(pk=candidate.case_id)
        line = ServiceCaseLine.objects.select_for_update().get(pk=candidate.pk)
        if case.state == ServiceCase.State.CLOSED:
            raise ValidationError(_('The service case is closed.'))
        event_type = serializer.validated_data['event_type']
        item = serializer.validated_data.get('stock_item') or line.stock_item
        item = (
            StockItem.objects
            .select_for_update()
            .select_related('location')
            .get(pk=item.pk)
        )
        if (
            item.pk != line.stock_item_id
            and item.pk != line.replacement_item_id
            and not line.events.filter(stock_item=item).exists()
        ):
            raise ValidationError({
                'stock_item': _('The item is not part of this service line.')
            })

        events = line.events.all()
        sent_quantity = events.filter(
            event_type=ServiceCaseEvent.EventType.SENT
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
        returned_quantity = events.filter(
            event_type=ServiceCaseEvent.EventType.RETURNED
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
        disposed_quantity = events.filter(
            event_type=ServiceCaseEvent.EventType.DISPOSED
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
        received_quantity = events.filter(
            event_type__in=[
                ServiceCaseEvent.EventType.RECEIVED,
                ServiceCaseEvent.EventType.RETURNED,
            ]
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
        inspected_quantity = events.filter(
            event_type=ServiceCaseEvent.EventType.INSPECTED
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)
        scrapped_quantity = events.filter(
            event_type=ServiceCaseEvent.EventType.SCRAPPED
        ).aggregate(total=Sum('quantity'))['total'] or Decimal(0)

        if event_type == ServiceCaseEvent.EventType.SENT:
            remaining_quantity = line.quantity - sent_quantity
        elif event_type == ServiceCaseEvent.EventType.RECEIVED:
            remaining_quantity = line.quantity - received_quantity
        elif event_type == ServiceCaseEvent.EventType.RETURNED:
            remaining_quantity = sent_quantity - returned_quantity - disposed_quantity
        elif event_type == ServiceCaseEvent.EventType.INSPECTED:
            remaining_quantity = received_quantity - inspected_quantity
        elif event_type == ServiceCaseEvent.EventType.DISPOSED:
            remaining_quantity = sent_quantity - returned_quantity - disposed_quantity
        elif event_type == ServiceCaseEvent.EventType.SCRAPPED:
            remaining_quantity = received_quantity - scrapped_quantity
        else:
            remaining_quantity = line.quantity

        quantity = Decimal(
            serializer.validated_data.get('quantity') or remaining_quantity
        )
        if quantity <= 0 or quantity > item.quantity:
            raise ValidationError({
                'quantity': _('Enter a positive quantity in stock.')
            })
        if quantity > remaining_quantity:
            raise ValidationError({
                'quantity': _('Quantity exceeds the remaining service line quantity.')
            })
        if item.serialized and quantity != 1:
            raise ValidationError({
                'quantity': _('Serialized service items must have quantity one.')
            })

        company = serializer.validated_data.get('company')
        expected_company = case.supplier or case.customer
        if (
            event_type
            in {
                ServiceCaseEvent.EventType.SENT,
                ServiceCaseEvent.EventType.EXTERNAL_RECEIVED,
                ServiceCaseEvent.EventType.RETURNED,
            }
            and not company
        ):
            raise ValidationError({
                'company': _('Select the external party for this hand-off.')
            })
        if (
            event_type == ServiceCaseEvent.EventType.RECEIVED
            and case.kind == ServiceCase.Kind.CUSTOMER_RETURN
            and not company
        ):
            raise ValidationError({
                'company': _('Select the customer returning this item.')
            })
        if expected_company and company and company.pk != expected_company.pk:
            raise ValidationError({
                'company': _('The party does not match the service case.')
            })

        from_location = item.location
        requested_from = serializer.validated_data.get('from_location')
        if requested_from and requested_from.pk != getattr(from_location, 'pk', None):
            raise ValidationError({
                'from_location': _('The source must match the current stock location.')
            })
        to_location = serializer.validated_data.get('to_location')
        notes = serializer.validated_data.get('notes', '').strip()
        target_status = None

        customer_return_receipt = (
            event_type == ServiceCaseEvent.EventType.RECEIVED
            and case.kind == ServiceCase.Kind.CUSTOMER_RETURN
        )
        if event_type in {
            ServiceCaseEvent.EventType.SENT,
            ServiceCaseEvent.EventType.RECEIVED,
            ServiceCaseEvent.EventType.RETURNED,
        }:
            if not from_location and not customer_return_receipt:
                raise ValidationError(
                    _('Move installed or unlocated stock to a location first.')
                )
            if not to_location:
                raise ValidationError({
                    'to_location': _('Select the destination location.')
                })
            if not customer_return_receipt and from_location.external != (
                event_type != ServiceCaseEvent.EventType.SENT
            ):
                raise ValidationError(
                    _('The item is not in the expected internal or external location.')
                )
            if to_location.external != (event_type == ServiceCaseEvent.EventType.SENT):
                raise ValidationError(
                    _('Choose the correct internal or external destination.')
                )
            if customer_return_receipt:
                shipment_order_id = (
                    case.source_shipment.order_id if case.source_shipment_id else None
                )
                belongs_to_customer = item.customer_id == case.customer_id or (
                    shipment_order_id is not None
                    and item.sales_order_id == shipment_order_id
                )
                if not belongs_to_customer:
                    raise ValidationError(
                        _('The returned item is not assigned to this customer.')
                    )
            if event_type in {
                ServiceCaseEvent.EventType.RECEIVED,
                ServiceCaseEvent.EventType.RETURNED,
            }:
                target_status = StockStatus.QUARANTINED.value
            elif event_type == ServiceCaseEvent.EventType.SENT:
                target_status = item.status
        elif event_type == ServiceCaseEvent.EventType.EXTERNAL_RECEIVED:
            if not from_location or not from_location.external:
                raise ValidationError(
                    _('External receipt requires stock at an external location.')
                )
        elif event_type == ServiceCaseEvent.EventType.INSPECTED:
            if not from_location or from_location.external:
                raise ValidationError(
                    _('Inspect the item after it returns to an internal location.')
                )
            passed = serializer.validated_data.get('inspection_passed')
            target_status = (
                StockStatus.OK.value if passed else StockStatus.REJECTED.value
            )
            to_location = from_location
        elif event_type == ServiceCaseEvent.EventType.DISPOSED:
            if not from_location or not from_location.external:
                raise ValidationError(
                    _('External disposal must be recorded at an external location.')
                )
            target_status = StockStatus.DESTROYED.value
            to_location = from_location
        elif event_type == ServiceCaseEvent.EventType.SCRAPPED:
            if not from_location or from_location.external:
                raise ValidationError(
                    _('Internal scrapping requires an internal stock location.')
                )
            target_status = StockStatus.DESTROYED.value
            to_location = from_location
        elif event_type == ServiceCaseEvent.EventType.REINSTALLED:
            if not case.unit_id or item.belongs_to_id != case.unit_id:
                raise ValidationError(
                    _('The item must be installed in the service case unit.')
                )

        if target_status is not None and customer_return_receipt:
            try:
                item.return_to_stock(
                    to_location,
                    self.request.user,
                    quantity=quantity,
                    merge=False,
                    status=target_status,
                    notes=notes,
                    tracking_code=StockHistoryCode.RETURNED_FROM_CUSTOMER,
                )
                item.refresh_from_db(fields=['status', 'status_custom_key'])
                if item.status != target_status:
                    raise ValidationError(
                        _('The returned stock did not reach quarantine status.')
                    )
            except DjangoValidationError as exc:
                raise ValidationError(
                    exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
                ) from exc
        elif target_status is not None:
            user = self.request.user
            try:
                if quantity < item.quantity:
                    moved_item = item.splitStock(
                        quantity, to_location, user, notes=notes, status=target_status
                    )
                    if moved_item is None:
                        raise ValidationError(
                            _('The stock quantity could not be split.')
                        )
                    item = moved_item
                elif event_type in {
                    ServiceCaseEvent.EventType.SENT,
                    ServiceCaseEvent.EventType.RECEIVED,
                    ServiceCaseEvent.EventType.RETURNED,
                }:
                    if not item.move(to_location, notes, user, status=target_status):
                        raise ValidationError(_('The stock item could not be moved.'))
                elif event_type in {
                    ServiceCaseEvent.EventType.INSPECTED,
                    ServiceCaseEvent.EventType.DISPOSED,
                    ServiceCaseEvent.EventType.SCRAPPED,
                }:
                    if not item.move(to_location, notes, user, status=target_status):
                        raise ValidationError(
                            _('The stock status could not be updated.')
                        )
                item.refresh_from_db(fields=['status', 'status_custom_key'])
                if item.status != target_status:
                    raise ValidationError(
                        _('The stock status did not reach the requested state.')
                    )
            except DjangoValidationError as exc:
                raise ValidationError(
                    exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
                ) from exc

        event = serializer.save(
            created_by=self.request.user,
            stock_item=item,
            quantity=quantity,
            from_location=from_location,
            to_location=to_location,
            company=company or expected_company,
        )
        if event.event_type == ServiceCaseEvent.EventType.SENT:
            case.state = ServiceCase.State.WAITING
        elif event.event_type in {
            ServiceCaseEvent.EventType.RETURNED,
            ServiceCaseEvent.EventType.RECEIVED,
        }:
            case.state = ServiceCase.State.INSPECTION
        elif event.event_type == ServiceCaseEvent.EventType.INSPECTED:
            case.state = ServiceCase.State.IN_PROGRESS
        case.save(update_fields=['state'])


class CountSessionViewSet(CangxuModelViewSet):
    """Snapshot stock at session start, review differences, then apply stocktake."""

    queryset = CountSession.objects.select_related(
        'location', 'started_by', 'reviewed_by'
    ).prefetch_related('lines__stock_item', 'lines__part')
    serializer_class = serializers.CountSessionSerializer
    filterset_fields = ['reference', 'location', 'state']
    ordering_fields = ['baseline_at', 'state']
    ordering = ['-baseline_at']

    @transaction.atomic
    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        location = serializer.validated_data['location']
        if location.structural:
            raise ValidationError({
                'location': _('A structural location cannot be counted.')
            })
        session = serializer.save(started_by=self.request.user)
        stock_items = (
            StockItem.objects
            .select_for_update()
            .filter(location=location, belongs_to__isnull=True, quantity__gt=0)
            .select_related('part')
        )
        CountLine.objects.bulk_create([
            CountLine(
                session=session,
                part=item.part,
                stock_item=item,
                expected_quantity=Decimal(1) if item.serialized else item.quantity,
            )
            for item in stock_items
        ])

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit(self, request, pk=None):
        """Submit the completed count session for review."""
        session = CountSession.objects.select_for_update().get(pk=self.get_object().pk)
        if session.state != CountSession.State.OPEN:
            raise ValidationError(_('Only an open count can be submitted.'))
        if (
            not session.lines.exists()
            or session.lines.filter(counted_quantity__isnull=True).exists()
        ):
            raise ValidationError(_('Count every line before submitting the session.'))
        session.state = CountSession.State.REVIEW
        session.save(update_fields=['state'])
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def close(self, request, pk=None):
        """Validate outstanding work and close the record."""
        session = CountSession.objects.select_for_update().get(pk=self.get_object().pk)
        if session.state != CountSession.State.REVIEW:
            raise ValidationError(
                _('The count session must be reviewed before closure.')
            )
        lines = list(session.lines.select_for_update())
        if not lines or any(
            line.counted_quantity is None or not line.reviewed for line in lines
        ):
            raise ValidationError(_('Every counted line requires independent review.'))

        stock_item_ids = [line.stock_item_id for line in lines if line.stock_item_id]
        stock_items = (
            StockItem.objects
            .select_for_update()
            .filter(pk__in=stock_item_ids)
            .in_bulk()
        )

        with batch_events(), batch_tracking_entries():
            for line in lines:
                item = stock_items.get(line.stock_item_id)
                if item is None:
                    raise ValidationError(
                        _(
                            'A count line without a stock record needs a receiving transaction first.'
                        )
                    )
                if item.location_id != session.location_id:
                    raise ValidationError(
                        _(
                            'Stock moved during this count. Reconcile its location before closing.'
                        )
                    )
                if item.updated and item.updated > session.baseline_at:
                    raise ValidationError(
                        _(
                            'Stock changed after the count baseline. Recount the affected line.'
                        )
                    )
                quantity = line.counted_quantity
                notes = f'Cangxu count {session.reference}: {line.discrepancy_reason}'
                if item.serialized and quantity == 0:
                    item.stocktake(
                        0, request.user, status=StockStatus.LOST, notes=notes
                    )
                else:
                    item.stocktake(quantity, request.user, notes=notes)

        session.state = CountSession.State.CLOSED
        session.reviewed_by = request.user
        session.closed_at = timezone.now()
        session.save(update_fields=['state', 'reviewed_by', 'closed_at'])
        return Response(self.get_serializer(session).data)


class CountLineViewSet(CangxuModelViewSet):
    """Capture physical counts and an explicit supervisor review."""

    queryset = CountLine.objects.select_related(
        'session', 'part', 'stock_item', 'counted_by'
    )
    serializer_class = serializers.CountLineSerializer
    filterset_fields = ['session', 'part', 'stock_item', 'reviewed']
    ordering_fields = ['id', 'part__name']
    http_method_names = ['get', 'patch', 'post', 'head', 'options']

    @transaction.atomic
    def perform_update(self, serializer):
        """Record the authorized physical count for this line."""
        session = CountSession.objects.select_for_update().get(
            pk=serializer.instance.session_id
        )
        line = CountLine.objects.select_for_update().get(pk=serializer.instance.pk)
        if session.state != CountSession.State.OPEN:
            raise ValidationError(_('Only open count lines can be counted.'))
        quantity = serializer.validated_data.get('counted_quantity')
        if quantity is None:
            raise ValidationError({'counted_quantity': _('Enter the physical count.')})
        if (
            quantity != line.expected_quantity
            and not serializer.validated_data.get(
                'discrepancy_reason', line.discrepancy_reason
            ).strip()
        ):
            raise ValidationError({
                'discrepancy_reason': _('Explain the count difference.')
            })
        serializer.save(counted_by=self.request.user, counted_at=timezone.now())

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def review(self, request, pk=None):
        """Record the supervisor review for this count line."""
        line_id = self.get_object().pk
        session_id = CountLine.objects.values_list('session_id', flat=True).get(
            pk=line_id
        )
        session = CountSession.objects.select_for_update().get(pk=session_id)
        line = CountLine.objects.select_for_update().get(pk=line_id)
        if session.state != CountSession.State.REVIEW:
            raise ValidationError(
                _('Submit the count session before reviewing a line.')
            )
        if line.counted_quantity is None:
            raise ValidationError(_('The line has not been counted.'))
        action_data = serializers.CountReviewSerializer(data=request.data)
        action_data.is_valid(raise_exception=True)
        if (
            line.counted_quantity != line.expected_quantity
            and not action_data.validated_data.get('note', '').strip()
        ):
            raise ValidationError({'note': _('A discrepancy review note is required.')})
        line.reviewed = True
        line.reviewed_by = request.user
        line.reviewed_at = timezone.now()
        if action_data.validated_data.get('note'):
            line.discrepancy_reason = (
                f'{line.discrepancy_reason}\nReview: {action_data.validated_data["note"]}'
            ).strip()
        line.save(
            update_fields=[
                'reviewed',
                'reviewed_by',
                'reviewed_at',
                'discrepancy_reason',
            ]
        )
        return Response(self.get_serializer(line).data)


class ShipmentManifestViewSet(CangxuModelViewSet):
    """Check package contents and freeze the scanned manifest."""

    queryset = ShipmentManifest.objects.select_related(
        'shipment', 'shipment__order', 'configuration', 'checked_by'
    ).prefetch_related('lines__stock_item__part')
    serializer_class = serializers.ShipmentManifestSerializer
    filterset_fields = ['shipment', 'configuration', 'package_code']
    search_fields = ['package_code', 'shipment__reference', 'shipment__tracking_number']
    ordering_fields = ['shipment__shipment_date', 'package_code', 'checked_at']

    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        shipment = serializer.validated_data['shipment']
        if shipment.shipment_date:
            raise ValidationError(_('A manifest cannot be edited after shipment.'))
        serializer.save()

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def verify(self, request, pk=None):
        """Record independent verification and complete the task."""
        manifest = ShipmentManifest.objects.select_for_update().get(
            pk=self.get_object().pk
        )
        if manifest.checked_at:
            raise ValidationError(_('This package manifest has already been checked.'))
        shipment = SalesOrderShipment.objects.select_for_update().get(
            pk=manifest.shipment_id
        )
        if shipment.shipment_date:
            raise ValidationError(_('A manifest cannot be edited after shipment.'))
        lines = list(manifest.lines.select_related('stock_item', 'stock_item__part'))
        if not lines:
            raise ValidationError(_('Scan the package contents before checking it.'))

        allocations = shipment.allocations.select_related('item')
        shipped_item_ids = {allocation.item_id for allocation in allocations}
        shipped_item_ids.update(
            item_id
            for allocation in allocations
            for item_id in allocation.item.installed_parts.values_list('pk', flat=True)
        )
        incorrect = [
            line.stock_item_id
            for line in lines
            if line.stock_item_id not in shipped_item_ids
        ]
        if incorrect:
            raise ValidationError({
                'lines': _('These items are not allocated to this shipment: %(items)s')
                % {'items': ', '.join(map(str, incorrect))}
            })

        if manifest.configuration:
            if manifest.configuration.state != UnitConfiguration.State.RELEASED:
                raise ValidationError(
                    _('Only a released configuration can be shipped.')
                )
            expected = set(
                manifest.configuration.items.filter(
                    removed_at__isnull=True
                ).values_list('component_id', flat=True)
            )
            actual = {line.stock_item_id for line in lines}
            if expected - actual:
                raise ValidationError({
                    'lines': _('The package is missing configured items: %(items)s')
                    % {'items': ', '.join(map(str, sorted(expected - actual)))}
                })

        snapshot = {
            'shipment': shipment.pk,
            'package_code': manifest.package_code,
            'configuration': manifest.configuration_id,
            'lines': [
                {
                    'stock_item': line.stock_item_id,
                    'part': line.stock_item.part_id,
                    'part_name': line.stock_item.part.name,
                    'serial': line.stock_item.serial,
                    'batch': line.stock_item.batch,
                    'quantity': str(line.quantity),
                    'role': line.item_role,
                }
                for line in sorted(lines, key=lambda value: value.stock_item_id)
            ],
        }
        encoded = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        )
        manifest.contents_snapshot = snapshot
        manifest.content_hash = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        manifest.checked_by = request.user
        manifest.checked_at = timezone.now()
        manifest.save(
            update_fields=[
                'contents_snapshot',
                'content_hash',
                'checked_by',
                'checked_at',
            ]
        )
        return Response(self.get_serializer(manifest).data)


class ShipmentManifestLineViewSet(CangxuModelViewSet):
    """Record scans until the parent package is verified."""

    queryset = ShipmentManifestLine.objects.select_related('manifest', 'stock_item')
    serializer_class = serializers.ShipmentManifestLineSerializer
    filterset_fields = ['manifest', 'stock_item', 'item_role']
    http_method_names = ['get', 'post', 'head', 'options']

    def perform_create(self, serializer):
        """Persist the validated object after workflow checks."""
        manifest = serializer.validated_data['manifest']
        if manifest.checked_at or manifest.shipment.shipment_date:
            raise ValidationError(_('A checked or shipped package cannot be changed.'))
        serializer.save()


class DataImportBatchViewSet(CangxuModelViewSet):
    """Stage source files and post only reviewed opening stock to InvenTree."""

    role_required = 'stock'
    queryset = DataImportBatch.objects.select_related(
        'created_by', 'reviewed_by'
    ).prefetch_related('records')
    serializer_class = serializers.DataImportBatchSerializer
    filterset_fields = ['source_system', 'source_kind', 'state']
    search_fields = ['source_system', 'source_file_name', 'source_file_digest']
    ordering_fields = ['created_at', 'source_kind', 'state']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """Parse an XLSX into traceable source rows without posting business data."""
        upload = request.FILES.get('source_file')
        if upload is None:
            raise ValidationError({'source_file': _('An XLSX file is required.')})
        if Path(upload.name).suffix.lower() != '.xlsx':
            raise ValidationError({
                'source_file': _('Only .xlsx workbooks are supported.')
            })
        if upload.size > 25 * 1024 * 1024:
            raise ValidationError({
                'source_file': _('The workbook exceeds the 25 MiB limit.')
            })

        digest = hashlib.sha256()
        for chunk in upload.chunks():
            digest.update(chunk)
        upload.seek(0)
        metadata = {
            'source_system': request.data.get('source_system', ''),
            'source_kind': request.data.get('source_kind', ''),
            'source_file_name': Path(upload.name).name[:255],
            'source_file_digest': digest.hexdigest(),
            'inventory_as_of': request.data.get('inventory_as_of'),
            'physical_count_confirmed': request.data.get(
                'physical_count_confirmed', False
            ),
        }
        serializer = self.get_serializer(data=metadata)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            source_rows = parse_workbook_rows(upload)
        except WorkbookImportError as exc:
            messages = {
                'workbook_too_large': _('The workbook exceeds the 25 MiB limit.'),
                'workbook_too_many_cells': _('The workbook exceeds the cell limit.'),
                'workbook_too_many_rows': _('The workbook exceeds the row limit.'),
                'workbook_has_no_populated_rows': _(
                    'The workbook contains no populated rows.'
                ),
                'invalid_xlsx': _('The uploaded file is not a readable XLSX workbook.'),
            }
            raise ValidationError({
                'source_file': messages.get(str(exc), _('Invalid workbook.'))
            }) from exc
        worksheet_rows = len(source_rows)
        rows = normalize_workbook_rows(source_rows, values['source_kind'])
        if not rows:
            raise ValidationError({
                'source_file': _('The workbook contains headers but no data rows.')
            })

        staged = 0
        with transaction.atomic():
            batch, created = DataImportBatch.objects.get_or_create(
                source_system=values['source_system'],
                source_kind=values['source_kind'],
                source_file_digest=values['source_file_digest'],
                defaults={
                    'source_file_name': values.get('source_file_name', ''),
                    'inventory_as_of': values.get('inventory_as_of'),
                    'physical_count_confirmed': values.get(
                        'physical_count_confirmed', False
                    ),
                    'created_by': request.user,
                },
            )
            if batch.state == DataImportBatch.State.DRAFT:
                before = batch.records.count()
                DataImportRecord.objects.bulk_create(
                    [DataImportRecord(batch=batch, **row) for row in rows],
                    ignore_conflicts=True,
                )
                staged = batch.records.count() - before

        return Response(
            {
                'batch': self.get_serializer(batch).data,
                'worksheet_rows': worksheet_rows,
                'data_rows': len(rows),
                'staged_rows': staged,
                'already_staged_rows': len(rows) - staged,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        """Return the original batch when the same source file is uploaded again."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        batch, created = DataImportBatch.objects.get_or_create(
            source_system=values['source_system'],
            source_kind=values['source_kind'],
            source_file_digest=values['source_file_digest'],
            defaults={
                'source_file_name': values.get('source_file_name', ''),
                'inventory_as_of': values.get('inventory_as_of'),
                'physical_count_confirmed': values.get(
                    'physical_count_confirmed', False
                ),
                'created_by': request.user,
            },
        )
        output = self.get_serializer(batch)
        return Response(
            output.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def perform_create(self, serializer):
        """Record the operator who staged the source."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def validate(self, request, pk=None):
        """Validate source mappings without mutating native inventory."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.state not in [
            DataImportBatch.State.DRAFT,
            DataImportBatch.State.REVIEW,
            DataImportBatch.State.PARTIAL,
        ]:
            raise ValidationError(
                _('This import batch cannot be validated in its current state.')
            )

        if not batch.records.exists():
            raise ValidationError(_('Stage at least one source row before validation.'))

        checked = 0
        valid = 0
        invalid = 0
        for record in batch.records.select_related('mapped_part', 'location').filter(
            state__in=[
                DataImportRecord.State.STAGED,
                DataImportRecord.State.INVALID,
                DataImportRecord.State.FAILED,
                DataImportRecord.State.VALID,
            ]
        ):
            errors = []
            if not isinstance(record.source_values, dict) or not record.source_values:
                errors.append({'field': 'source_values', 'code': 'invalid_object'})
            errors.extend(validate_normalized_import_values(record.normalized_values))

            if batch.source_kind == DataImportBatch.Kind.OPENING_STOCK:
                if not record.mapped_part_id:
                    errors.append({'field': 'mapped_part', 'code': 'required'})
                if not record.location_id or record.location.external:
                    errors.append({
                        'field': 'location',
                        'code': 'internal_location_required',
                    })
                if record.quantity is None or record.quantity <= 0:
                    errors.append({
                        'field': 'quantity',
                        'code': 'positive_quantity_required',
                    })
                if not record.batch_code.strip():
                    errors.append({'field': 'batch_code', 'code': 'required'})

                if record.mapped_part_id:
                    if record.mapped_part.trackable:
                        if not record.serial.strip():
                            errors.append({
                                'field': 'serial',
                                'code': 'required_for_trackable_part',
                            })
                        if record.quantity is not None and record.quantity != 1:
                            errors.append({
                                'field': 'quantity',
                                'code': 'serialized_quantity_must_be_one',
                            })
                    elif record.serial.strip():
                        errors.append({'field': 'serial', 'code': 'not_trackable'})

                    if (
                        record.serial.strip()
                        and StockItem.objects.filter(
                            part=record.mapped_part,
                            serial__iexact=record.serial.strip(),
                        ).exists()
                    ):
                        errors.append({
                            'field': 'serial',
                            'code': 'already_exists_for_part',
                        })
            else:
                errors.append({
                    'field': 'source_kind',
                    'code': 'type_specific_validation_not_implemented',
                })

            record.validation_errors = errors
            record.state = (
                DataImportRecord.State.INVALID
                if errors
                else DataImportRecord.State.VALID
            )
            record.apply_error = ''
            record.save(update_fields=['validation_errors', 'state', 'apply_error'])
            checked += 1
            if errors:
                invalid += 1
            else:
                valid += 1

        batch.state = DataImportBatch.State.REVIEW
        batch.save(update_fields=['state'])
        return Response({
            'batch': batch.pk,
            'checked': checked,
            'valid': valid,
            'invalid': invalid,
        })

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        """Approve a fully valid batch after opening-balance prerequisites."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.state not in [
            DataImportBatch.State.REVIEW,
            DataImportBatch.State.PARTIAL,
        ]:
            raise ValidationError(_('Validate this batch before approval.'))
        if not batch.records.exists():
            raise ValidationError(_('An empty batch cannot be approved.'))
        if batch.records.exclude(
            state__in=[
                DataImportRecord.State.VALID,
                DataImportRecord.State.APPLIED,
                DataImportRecord.State.REJECTED,
            ]
        ).exists():
            raise ValidationError(
                _('Resolve every invalid or failed row before approval.')
            )
        if not batch.records.filter(
            state__in=[DataImportRecord.State.VALID, DataImportRecord.State.APPLIED]
        ).exists():
            raise ValidationError(_('Approve at least one valid row.'))
        if batch.source_kind == DataImportBatch.Kind.OPENING_STOCK and (
            not batch.inventory_as_of or not batch.physical_count_confirmed
        ):
            raise ValidationError({
                'inventory_as_of': _(
                    'Confirm the opening-balance date and physical count before approval.'
                )
            })

        batch.records.filter(state=DataImportRecord.State.VALID).update(
            state=DataImportRecord.State.APPROVED
        )
        batch.state = DataImportBatch.State.APPROVED
        batch.reviewed_by = request.user
        batch.reviewed_at = timezone.now()
        batch.save(update_fields=['state', 'reviewed_by', 'reviewed_at'])
        return Response(self.get_serializer(batch).data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reject(self, request, pk=None):
        """Reject a batch before posting while retaining every source row."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.records.filter(state=DataImportRecord.State.APPLIED).exists():
            raise ValidationError(
                _('A batch with applied inventory cannot be rejected.')
            )
        if batch.state in [
            DataImportBatch.State.APPLIED,
            DataImportBatch.State.REJECTED,
        ]:
            raise ValidationError(_('This import batch is already closed.'))
        note = serializers.CountReviewSerializer(data=request.data)
        note.is_valid(raise_exception=True)
        reason = note.validated_data.get('note', '').strip()
        if not reason:
            raise ValidationError({
                'note': _('Provide a reason for rejecting the batch.')
            })

        for record in batch.records.exclude(state=DataImportRecord.State.APPLIED):
            record.state = DataImportRecord.State.REJECTED
            record.validation_errors = [
                {'field': 'review', 'code': 'batch_rejected', 'note': reason}
            ]
            record.save(update_fields=['state', 'validation_errors'])
        batch.state = DataImportBatch.State.REJECTED
        batch.reviewed_by = request.user
        batch.reviewed_at = timezone.now()
        batch.save(update_fields=['state', 'reviewed_by', 'reviewed_at'])
        return Response(self.get_serializer(batch).data)

    @action(detail=True, methods=['post'], url_path='stage-rows')
    @transaction.atomic
    def stage_rows(self, request, pk=None):
        """Store spreadsheet rows in bulk without changing native business data."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.state != DataImportBatch.State.DRAFT:
            raise ValidationError(_('Rows can only be staged in a draft batch.'))
        if not isinstance(request.data, list) or not request.data:
            raise ValidationError(_('Provide a non-empty list of source rows.'))

        row_serializer = serializers.DataImportStageRowSerializer(
            data=request.data, many=True
        )
        row_serializer.is_valid(raise_exception=True)
        values = row_serializer.validated_data
        keys = [(row['source_sheet'], row['source_row']) for row in values]
        if len(keys) != len(set(keys)):
            raise ValidationError(
                _('The request contains duplicate source row locations.')
            )

        existing_count = batch.records.count()
        records = [DataImportRecord(batch=batch, **row) for row in values]
        DataImportRecord.objects.bulk_create(records, ignore_conflicts=True)
        created = batch.records.count() - existing_count
        return Response(
            {
                'batch': batch.pk,
                'submitted': len(records),
                'created': created,
                'already_staged': len(records) - created,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='map-opening-stock')
    @transaction.atomic
    def map_opening_stock(self, request, pk=None):
        """Resolve staged part codes and defaults without creating stock records."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.source_kind != DataImportBatch.Kind.OPENING_STOCK:
            raise ValidationError(_('Only opening stock batches can use this mapping.'))
        if batch.state != DataImportBatch.State.DRAFT:
            raise ValidationError(_('Only draft batches can be mapped.'))

        mapping = serializers.OpeningStockMappingSerializer(data=request.data)
        mapping.is_valid(raise_exception=True)
        location = mapping.validated_data['location']
        mapped = 0
        unresolved = 0
        for record in batch.records.select_for_update().filter(
            state__in=[DataImportRecord.State.STAGED, DataImportRecord.State.INVALID]
        ):
            normalized = record.normalized_values
            if normalized.get('row_type') == 'header':
                continue
            fields = normalized.get('fields', {})
            if not isinstance(fields, dict):
                fields = {}

            row_errors = []
            codes = [fields.get('part_number'), fields.get('oem_part_number')]
            codes = [
                code.strip() for code in codes if isinstance(code, str) and code.strip()
            ]
            candidate_ids = set()
            if codes:
                part_query = Q()
                for code in codes:
                    part_query |= Q(IPN__iexact=code)
                candidate_ids.update(
                    Part.objects.filter(part_query).values_list('pk', flat=True)
                )
                candidate_ids.update(
                    PartCodeAlias.objects
                    .filter(normalized_code__in=[code.upper() for code in codes])
                    .filter(Q(source_system=batch.source_system) | Q(source_system=''))
                    .values_list('part_id', flat=True)
                )

            if len(candidate_ids) > 1:
                row_errors.append({
                    'field': 'part_number',
                    'code': 'ambiguous_part_code',
                })
            elif candidate_ids:
                candidate_id = candidate_ids.pop()
                if record.mapped_part_id not in [None, candidate_id]:
                    row_errors.append({
                        'field': 'mapped_part',
                        'code': 'manual_mapping_conflicts_with_part_code',
                    })
                else:
                    record.mapped_part_id = candidate_id
            elif not record.mapped_part_id:
                row_errors.append({
                    'field': 'part_number',
                    'code': 'part_code_not_resolved' if codes else 'part_code_required',
                })

            if record.location_id not in [None, location.pk]:
                row_errors.append({
                    'field': 'location',
                    'code': 'location_mapping_conflict',
                })
            else:
                record.location = location

            source_quantity = fields.get('quantity')
            if source_quantity not in (None, ''):
                try:
                    quantity = Decimal(str(source_quantity))
                    if quantity <= 0:
                        raise ValueError
                    if record.quantity not in [None, quantity]:
                        row_errors.append({
                            'field': 'quantity',
                            'code': 'quantity_mapping_conflict',
                        })
                    else:
                        record.quantity = quantity
                except Exception:
                    row_errors.append({'field': 'quantity', 'code': 'invalid_quantity'})

            for field, source_field in [
                ('serial', 'serial'),
                ('batch_code', 'batch_code'),
            ]:
                source_value = fields.get(source_field)
                if source_value in (None, ''):
                    continue
                if not isinstance(source_value, str):
                    row_errors.append({'field': field, 'code': f'{field}_must_be_text'})
                    continue
                source_value = source_value.strip()
                current_value = getattr(record, field)
                if current_value and current_value != source_value:
                    row_errors.append({
                        'field': field,
                        'code': f'{field}_mapping_conflict',
                    })
                else:
                    setattr(record, field, source_value)

            record.validation_errors = row_errors
            record.apply_error = ''
            record.state = (
                DataImportRecord.State.INVALID
                if row_errors
                else DataImportRecord.State.STAGED
            )
            record.save()
            if row_errors:
                unresolved += 1
            else:
                mapped += 1

        return Response({
            'batch': batch.pk,
            'mapped': mapped,
            'unresolved': unresolved,
            'rows': batch.records.count(),
        })

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def apply(self, request, pk=None):
        """Create native StockItem and lot records for approved opening rows."""
        batch = DataImportBatch.objects.select_for_update().get(pk=self.get_object().pk)
        if batch.source_kind != DataImportBatch.Kind.OPENING_STOCK:
            raise ValidationError(
                _(
                    'This source type is staged for review but has no native apply workflow yet.'
                )
            )
        if batch.state == DataImportBatch.State.APPLIED:
            return Response({
                'batch': batch.pk,
                'applied': 0,
                'failed': 0,
                'already_applied': True,
            })
        if batch.state not in [
            DataImportBatch.State.APPROVED,
            DataImportBatch.State.PARTIAL,
        ]:
            raise ValidationError(_('Approve this batch before applying it.'))

        applied = 0
        failed = 0
        for candidate in batch.records.filter(state=DataImportRecord.State.APPROVED):
            try:
                with transaction.atomic():
                    record = (
                        DataImportRecord.objects
                        .select_for_update()
                        .select_related('mapped_part', 'location')
                        .get(pk=candidate.pk)
                    )
                    item = StockItem.objects.create(
                        part=record.mapped_part,
                        location=record.location,
                        quantity=record.quantity,
                        serial=record.serial.strip() or None,
                        batch=record.batch_code.strip(),
                        status=StockStatus.OK.value,
                    )
                    lot, _lot_created = ManufacturingLot.objects.get_or_create(
                        part=record.mapped_part,
                        code=record.batch_code.strip(),
                        defaults={
                            'notes': (
                                f'Opening balance imported from approved batch {batch.pk}; '
                                'see source row for provenance.'
                            )
                        },
                    )
                    ManufacturingLotStockItem.objects.get_or_create(
                        lot=lot, stock_item=item
                    )
                    record.stock_item = item
                    record.state = DataImportRecord.State.APPLIED
                    record.applied_at = timezone.now()
                    record.apply_error = ''
                    record.save(
                        update_fields=[
                            'stock_item',
                            'state',
                            'applied_at',
                            'apply_error',
                        ]
                    )
                applied += 1
            except Exception as exc:
                DataImportRecord.objects.filter(pk=candidate.pk).update(
                    state=DataImportRecord.State.FAILED, apply_error=str(exc)[:500]
                )
                failed += 1

        pending = batch.records.filter(state=DataImportRecord.State.APPROVED).exists()
        batch.state = (
            DataImportBatch.State.PARTIAL
            if failed or pending
            else DataImportBatch.State.APPLIED
        )
        if batch.state == DataImportBatch.State.APPLIED:
            batch.applied_at = timezone.now()
        batch.save(update_fields=['state', 'applied_at'])
        return Response({'batch': batch.pk, 'applied': applied, 'failed': failed})


class DataImportRecordViewSet(CangxuModelViewSet):
    """Preview source rows and correct normalized mappings before approval."""

    role_required = 'stock'
    queryset = DataImportRecord.objects.select_related(
        'batch', 'mapped_part', 'location', 'stock_item'
    )
    serializer_class = serializers.DataImportRecordSerializer
    filterset_fields = ['batch', 'state', 'mapped_part', 'location']
    search_fields = ['source_sheet', 'source_range', 'serial', 'batch_code']
    ordering_fields = ['source_sheet', 'source_row', 'state', 'created_at']
    ordering = ['batch', 'source_sheet', 'source_row']

    def perform_create(self, serializer):
        """Only append source rows while their batch is still a draft."""
        batch = serializer.validated_data['batch']
        if batch.state != DataImportBatch.State.DRAFT:
            raise ValidationError(_('Rows can only be added to a draft batch.'))
        serializer.save()

    def perform_update(self, serializer):
        """Reset validation after a corrected mapping is saved."""
        record = self.get_object()
        if record.state in [
            DataImportRecord.State.APPROVED,
            DataImportRecord.State.APPLIED,
            DataImportRecord.State.REJECTED,
        ]:
            raise ValidationError(_('Approved or applied source rows are immutable.'))
        serializer.save(
            state=DataImportRecord.State.STAGED, validation_errors=[], apply_error=''
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def reject(self, request, pk=None):
        """Reject one source row while retaining its original values for audit."""
        record = DataImportRecord.objects.select_for_update().get(
            pk=self.get_object().pk
        )
        if record.state in [
            DataImportRecord.State.APPROVED,
            DataImportRecord.State.APPLIED,
            DataImportRecord.State.REJECTED,
        ]:
            raise ValidationError(_('This source row can no longer be rejected.'))
        note = serializers.CountReviewSerializer(data=request.data)
        note.is_valid(raise_exception=True)
        record.state = DataImportRecord.State.REJECTED
        record.validation_errors = [
            {
                'field': 'review',
                'code': 'rejected',
                'note': note.validated_data.get('note', ''),
            }
        ]
        record.save(update_fields=['state', 'validation_errors'])
        return Response(self.get_serializer(record).data)


router = DefaultRouter()
router.register('part-aliases', PartCodeAliasViewSet, basename='cangxu-part-alias')
router.register(
    'hardware-profiles',
    HardwareProfileRevisionViewSet,
    basename='cangxu-hardware-profile',
)
router.register(
    'hardware-ports', HardwarePortDefinitionViewSet, basename='cangxu-hardware-port'
)
router.register('cable-ends', CableEndDefinitionViewSet, basename='cangxu-cable-end')
router.register('lots', ManufacturingLotViewSet, basename='cangxu-lot')
router.register(
    'lot-partners', ManufacturingLotPartnerViewSet, basename='cangxu-lot-partner'
)
router.register(
    'lot-stock-items',
    ManufacturingLotStockItemViewSet,
    basename='cangxu-lot-stock-item',
)
router.register(
    'configurations', UnitConfigurationViewSet, basename='cangxu-configuration'
)
router.register(
    'configuration-items',
    ConfigurationItemViewSet,
    basename='cangxu-configuration-item',
)
router.register(
    'configuration-tests',
    ConfigurationTestEvidenceViewSet,
    basename='cangxu-configuration-test',
)
router.register(
    'component-replacements',
    ComponentReplacementViewSet,
    basename='cangxu-component-replacement',
)
router.register('quality-issues', QualityIssueViewSet, basename='cangxu-quality-issue')
router.register('rework-tasks', ReworkTaskViewSet, basename='cangxu-rework-task')
router.register('service-cases', ServiceCaseViewSet, basename='cangxu-service-case')
router.register('service-lines', ServiceCaseLineViewSet, basename='cangxu-service-line')
router.register(
    'service-events', ServiceCaseEventViewSet, basename='cangxu-service-event'
)
router.register('count-sessions', CountSessionViewSet, basename='cangxu-count-session')
router.register('count-lines', CountLineViewSet, basename='cangxu-count-line')
router.register(
    'shipment-manifests', ShipmentManifestViewSet, basename='cangxu-manifest'
)
router.register(
    'manifest-lines', ShipmentManifestLineViewSet, basename='cangxu-manifest-line'
)
router.register(
    'import-batches', DataImportBatchViewSet, basename='cangxu-import-batch'
)
router.register(
    'import-records', DataImportRecordViewSet, basename='cangxu-import-record'
)

urlpatterns = router.urls
