"""Models for approval."""
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import InvenTree.models
import users.models
from generic.states import StatusCode

from .defaults import DefaultApprovalRules


class ApprovalState(StatusCode):
    """Defines a set of status codes for an Approval."""

    NEW = 0, _("New"), "secondary"  # Approval is new
    PENDING = 10, _("Pending"), "secondary"  # Approval is pending - ie there were some decisions but nothing final
    APPROVED = 20, _("Approved"), "success"  # Approval has been approved
    REJECTED = 30, _("Rejected"), "danger"  # Approval has been rejected
    CANCELLED = 40, _("Cancelled"), "warning"  # Approval has been cancelled
    EXPIRED = 50, _("Expired"), "warning"  # Approval has expired


class ApprovalStateGroups:
    """Groups for ApprovalState codes."""

    # Open approvals
    OPEN = [
        ApprovalState.NEW.value,
        ApprovalState.PENDING.value,
    ]

    # Completed approvals
    COMPLETE = [
        ApprovalState.APPROVED.value,
        ApprovalState.REJECTED.value,
        ApprovalState.CANCELLED.value,
        ApprovalState.EXPIRED.value,
    ]


# TODO @matmair add tracking
class Approval(
    InvenTree.models.MetadataMixin,
    InvenTree.models.ReferenceIndexingMixin,
    models.Model,
):
    """An approval is a process in which an outcome is reached based on a set of rules.

    Approvals have different states and can not be modified once they are finalised.
    The rule set for a an approval has to be set at creation time and can not be modified afterwards. The rules itself however can have dynamic components.

    Args:
        creation_date (datetime): Date and time of creation
        created_by (User): User that created the approval
        modified_by (User): User that last modified the approval
        modified_date (datetime): Date and time of last modification
        finalised (bool): True if the approval is finalised
        finalised_date (datetime): Date and time of finalisation
        finalised_by (User): User that finalised the approval
        responsible (Owner): User or group responsible for this approval
        owner (Owner): User or group that owns this approval
        name (str): Name of the approval
        description (str): Description of the approval
        reference (str): Reference of the approval
        data (JSON): Data of the approval
        status (int): Status of the approval
        content_type (ContentType): Content type of the approval
        object_id (int): Object id of the approval
        content_object (GenericForeignKey): Link to the linked object of the approval
    """

    class Meta:
        """Meta class."""

        verbose_name = _("Approval")
        verbose_name_plural = _("Approvals")

    def __str__(self):
        """Pretty string."""
        prefix = f"{self.reference}: " if self.reference else ""
        return f"{prefix}{self.name} ({self.status})"

    creation_date = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_("Creation date")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Created by"),
        related_name="approvals_created",
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Last modified by"),
        related_name="approvals_modified",
    )
    modified_date = models.DateTimeField(
        auto_now=True, editable=False, verbose_name=_("Last modified date")
    )
    finalised = models.BooleanField(default=False, verbose_name=_("Finalised"))
    finalised_date = models.DateTimeField(
        null=True, blank=True, editable=False, verbose_name=_("Finalisation date")
    )
    finalised_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Finalised by"),
        related_name="approvals_finalised",
    )
    responsible = models.ForeignKey(
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Responsible"),
        help_text=_("User or group responsible for this approval"),
        related_name="approvals_responsible",
    )
    owner = models.ForeignKey(
        users.models.Owner,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Owner"),
        help_text=_("User or group that owns this approval"),
        related_name="approvals_owned",
    )

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    reference = models.CharField(
        max_length=100, blank=True, verbose_name=_("Reference")
    )
    data = models.JSONField(blank=True, null=True, verbose_name=_("Data"))
    status = models.PositiveIntegerField(
        verbose_name=_("Status"),
        default=ApprovalState.NEW.value,
        choices=ApprovalState.items(),
        validators=[MinValueValidator(0)],
        help_text=_("Approval status"),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    _STATE_CHECKING = False  # Flag to prevent recursive state checking

    @property
    def status_label(self):
        """Return label."""
        return ApprovalState.label(self.status)

    @property
    def status_text(self):
        """Return the text representation of the status field"""
        return ApprovalState.text(self.status)

    def get_api_url(self):
        """Return API detail URL for this object."""
        return reverse("api-approval-detail", kwargs={"pk": self.id})

    def get_absolute_url(self):
        """Return url for instance."""
        return reverse("api-approval-detail", kwargs={"pk": self.id})

    def save(self, *args, **kwargs):
        """Custom save method to enforce business logic.

        Rules:
        - If the approval is finalised, it can not be modified anymore
        - The reference field is automatically generated if it is empty
        - The reference_int field is automatically updated any time

        """
        if self.finalised:
            # Check if the approval is alyread finalised - then we fail hard
            if Approval.objects.get(pk=self.pk).finalised is True:
                raise ValidationError(
                    _("Approval is already finalised and can not be modified anymore.")
                )

            # We are sure this was not finalised before, so we can set the finalisation date and user
            self.finalised_date = datetime.now()
            self.finalised_by = self.modified_by

        self.reference_int = self.rebuild_reference_field(self.reference)

        if not self.creation_date:
            self.creation_date = datetime.now().date()

        # Check state of the approval
        if not self._STATE_CHECKING:
            self.check_approval_state(no_save=True)

        super().save(*args, **kwargs)

    @classmethod
    def api_defaults(cls, request):
        """Return default values for this model when issuing an API OPTIONS request"""

        defaults = {
            'reference': generate_next_purchase_approval_reference(),
        }

        return defaults

    def add_decision(self, user: User, value: bool, comment: str = ''):
        """Add a decision for this approval"""
        new_decision = ApprovalDecision.objects.create(
            approval=self,
            user=user,
            decision=value,
            comment=comment
        )
        return new_decision

    def check_approval_state(self, no_save: bool = False):
        """Re-check current approval state."""
        # If the approval is finished there is no reason to check again
        if self.finalised:
            return self.status

        self._STATE_CHECKING = True

        # Iterate over all decisions
        decisions = self.decisions.all()

        # Check all default rules
        for rule in DefaultApprovalRules:
            val = rule().check(approval=self, target=self.content_object, decisions=decisions)
            if val is not None:
                if val:
                    return self.handle_approval(no_save=no_save)
                return self.handle_rejection(no_save=no_save)

        # If there is more than 0 decision we are pending
        if len(decisions) > 0:
            self.status = ApprovalState.PENDING.value
            if not no_save:
                self.save()
            return self.status

    def handle_approval(self, no_save: bool = False):
        """Handle approval."""
        self.status = ApprovalState.APPROVED.value
        self.finalised = True
        if not no_save:
            self.save()
        return self.status

    def handle_rejection(self, no_save: bool = False):
        """Handle rejection."""
        self.status = ApprovalState.REJECTED.value
        self.finalised = True
        if not no_save:
            self.save()
        return self.status


def generate_next_purchase_approval_reference():
    """Generate the next available Approval reference"""

    return Approval.generate_reference()


class ApprovalDecision(InvenTree.models.MetadataMixin, models.Model):
    """A decision is a single decision made in an approval process.

    Decisions are made by users and can be changed by them - if the approval is not finished.
    """

    class Meta:
        """Model meta options."""

        verbose_name = _("Approval decision")
        verbose_name_plural = _("Approval decisions")
        unique_together = [('approval', 'user'), ]

    def __str__(self):
        """Pretty string."""
        return f"{self.user}: {self.decision} ({self.date})"

    approval = models.ForeignKey(
        Approval, on_delete=models.CASCADE, verbose_name=_("Approval"),
        related_name='decisions',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    date = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_("Date")
    )
    decision = models.BooleanField(verbose_name=_("Decision"))
    comment = models.TextField(blank=True, verbose_name=_("Comment"))

    def get_api_url(self):
        """Return API detail URL for this object."""
        return reverse("api-approval-decision-detail", kwargs={"pk": self.id})

    def get_absolute_url(self):
        """Return url for instance."""
        return reverse("api-approval-decision-detail", kwargs={"pk": self.id})

    def save(self, *args, **kwargs):
        """Custom save method to enforce business logic.

        Rules:
        - If the approval is finalised, it can not be modified anymore
        - Always update the modified info of the approval when adding a decision
        """
        if self.approval.finalised:
            raise ValidationError(
                _("Approval is already finalised and can not be modified anymore.")
            )

        with transaction.atomic():

            # Update the modified info of the approval
            self.approval.modified_date = datetime.now()
            self.approval.modified_by = self.user
            self.approval.save()

            super().save(*args, **kwargs)

            # Check state of approval
            self.approval.status = self.approval.check_approval_state()
