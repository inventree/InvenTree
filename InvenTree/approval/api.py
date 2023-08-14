"""API views for the Approval app."""
from django.contrib.contenttypes.models import ContentType
from django.urls import include, path, re_path

from rest_framework import serializers

from InvenTree.api import MetadataView
from InvenTree.helpers import str2bool
from InvenTree.mixins import CreateAPI, ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.serializers import InvenTreeModelSerializer, UserSerializer
from users.serializers import OwnerSerializer

from .models import Approval, ApprovalDecision


class UserDetailApiMixin:
    """Mixin to add extra context information regarding user/owner details to endpoint serializers."""

    def get_serializer(self, *args, **kwargs):
        """Add extra context information to the endpoint serializer."""
        try:
            user_detail = str2bool(self.request.GET.get('user_detail', None))
        except AttributeError:
            user_detail = None

        kwargs['user_detail'] = user_detail
        return self.serializer_class(*args, **kwargs)


class UserDetailSerializerMixin:
    """Mixin to determine if extra serializer fields are required."""

    def __init__(self, *args, **kwargs):
        """Determine if extra serializer fields are required"""
        user_detail = kwargs.pop('user_detail', False)

        super().__init__(*args, **kwargs)

        if user_detail is not True:
            for field in self.Meta.user_detail_fields:
                self.fields.pop(field)


class TaggedObjectRelatedField(serializers.RelatedField):
    """A custom field to use for the `tagged_object` generic relationship."""

    def to_representation(self, value):
        """Serialize tagged objects to a simple textual representation."""
        if hasattr(value, 'get_api_url'):
            return f'{value.get_api_url()}{value.id}/'
        if hasattr(value, 'get_absolute_url'):
            return value.get_absolute_url()
        else:
            return value.id


class ApprovalDecisionSerializer(UserDetailSerializerMixin, InvenTreeModelSerializer):
    """Serializes an ApprovalDecision object"""

    user_detail = UserSerializer(source='user', read_only=True, many=False)

    class Meta:
        """Meta data for ApprovalDecisionSerializer"""
        model = ApprovalDecision
        exclude = [
            'metadata',
        ]
        user_detail_fields = ['user_detail',]

    def is_valid(self, *, raise_exception=False):
        """Insert user to save request."""
        request = self.context['request']
        self.initial_data['user'] = request.user.pk
        return super().is_valid(raise_exception=raise_exception)


class ApprovalSerializer(UserDetailSerializerMixin, InvenTreeModelSerializer):
    """Serializes an Approval object"""

    status_text = serializers.CharField(source='get_status_display', read_only=True)
    content_object = TaggedObjectRelatedField(read_only=True)
    model = serializers.CharField(required=False, write_only=True)
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)
    creation_date = serializers.DateTimeField(format='iso-8601', required=False)
    created_by_detail = UserSerializer(source='created_by', read_only=True, many=False)
    modified_date = serializers.DateTimeField(format='iso-8601', required=False)
    modified_by_detail = UserSerializer(source='modified_by', read_only=True, many=False)
    finalised_date = serializers.DateTimeField(format='iso-8601', required=False)
    finalised_by_detail = UserSerializer(source='finalised_by', read_only=True, many=False)
    responsible_detail = OwnerSerializer(source='responsible', read_only=True)
    owner_detail = OwnerSerializer(source='owner', read_only=True)

    class Meta:
        """Meta data for ApprovalSerializer"""
        model = Approval
        exclude = [
            'reference_int',
            'metadata',
            'data',
            # 'object_id',
            # 'content_type',
        ]

        read_only_fields = [
            'creation_date',
            'finalised_date',
            'modified_date',
        ]

        user_detail_fields = [
            'created_by_detail',
            'modified_by_detail',
            'finalised_by_detail',
            'responsible_detail',
            'owner_detail',
        ]

    def is_valid(self, *, raise_exception=False):
        """User optional field 'model' to determine content_type."""
        if 'model' in self.initial_data:
            model = self.initial_data.pop('model')
            mdl_splt = model.split('.')
            content_type = ContentType.objects.get(app_label=mdl_splt[0], model=mdl_splt[1])
            self.initial_data['content_type'] = content_type.pk
        return super().is_valid(raise_exception=raise_exception)


class ApprovalList(UserDetailApiMixin, ListCreateAPI):
    """API endpoint for listing all Approval objects"""

    queryset = Approval.objects.all()
    serializer_class = ApprovalSerializer
    filterset_fields = [
        "owner",
        "status",
        "content_type",
        "object_id",
    ]
    search_fields = [
        "name",
        "description",
        "reference",
    ]
    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
    }
    ordering_fields = [
        "name",
        "status",
        "finalised_date",
        "modified_date",
        "created_date",
        'reference',
    ]
    ordering = '-reference'

    def clean_data(self, data: dict) -> dict:
        """Custom clean_data method to add current user."""
        data = super().clean_data(data)
        data['created_by'] = self.request.user.pk
        return data


class ApprovalDetail(UserDetailApiMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of an Approval object"""

    queryset = Approval.objects.all()
    serializer_class = ApprovalSerializer


class ApprovalDecisionList(UserDetailApiMixin, ListCreateAPI):
    """API endpoint for listing all ApprovalDecision objects"""

    queryset = ApprovalDecision.objects.all()
    serializer_class = ApprovalDecisionSerializer
    filterset_fields = [
        "approval",
        "user",
        "status",
    ]
    search_fields = [
        "comment",
    ]
    ordering_fields = [
        "approval",
        "user",
        "status",
        "date",
    ]


class ApprovalDecisionDetail(UserDetailApiMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of an ApprovalDecision object"""

    queryset = ApprovalDecision.objects.all()
    serializer_class = ApprovalDecisionSerializer


class ApprovalApproveSerializer(InvenTreeModelSerializer):
    """Serializes an ApprovalDecision object"""

    class Meta:
        """Meta data for ApprovalDecisionSerializer"""
        model = ApprovalDecision
        exclude = ['metadata',]

    def is_valid(self, *, raise_exception=False):
        """Insert data to save request."""
        request = self.context['request']
        self.initial_data['user'] = request.user.pk
        self.initial_data['approval'] = request.parser_context['kwargs'].get('pk', None)
        self.initial_data['decision'] = True
        return super().is_valid(raise_exception=raise_exception)


class ApproveView(CreateAPI):
    """API endpoint to approve approval."""

    queryset = ApprovalDecision.objects.all()
    serializer_class = ApprovalApproveSerializer


detail_api = [
    re_path(r"^decision/", include([
        re_path(r"^$", ApprovalDecisionList.as_view(), name="api-approval-decision-list",),
        re_path(r"^(?P<pk>\d+)/", ApprovalDecisionDetail.as_view(), name="api-approval-decision-detail",),
    ])),
    re_path('approve/', ApproveView.as_view(), name='api-approval-approve'),
    re_path(r'^metadata/', MetadataView.as_view(), {'model': Approval}, name='api-approval-metadata'),
    re_path(r'^.*$', ApprovalDetail.as_view(), name='api-approval-detail'),
]


approval_api_urls = [
    path(r'<str:type>:<int:pk>/', include(detail_api)),
    path(r'<int:pk>/', include(detail_api)),
    re_path(r'^.*$', ApprovalList.as_view(), name='api-approval-list'),
]
