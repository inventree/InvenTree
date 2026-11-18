"""Build summaries for related objects without importing stock serializers."""

from generic.states.fields import InvenTreeCustomStatusSerializerMixin
from InvenTree.serializers import InvenTreeModelSerializer

from .models import Build


class BuildBriefSerializer(
    InvenTreeCustomStatusSerializerMixin, InvenTreeModelSerializer
):
    """Serialize build identity and status for related-object detail fields."""

    class Meta:
        """Serializer options."""

        model = Build
        fields = ['pk', 'reference', 'title', 'status', 'status_custom_key']
        read_only_fields = fields
