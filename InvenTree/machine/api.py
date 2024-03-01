"""JSON API for the machine app."""

from django.urls import include, path, re_path

from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

import machine.serializers as MachineSerializers
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateAPI, RetrieveUpdateDestroyAPI
from machine import registry
from machine.models import MachineConfig, MachineSetting


class MachineList(ListCreateAPI):
    """API endpoint for list of Machine objects.

    - GET: Return a list of all Machine objects
    - POST: create a MachineConfig
    """

    queryset = MachineConfig.objects.all()
    serializer_class = MachineSerializers.MachineConfigSerializer

    def get_serializer_class(self):
        """Allow driver, machine_type fields on creation."""
        if self.request.method == 'POST':
            return MachineSerializers.MachineConfigCreateSerializer
        return super().get_serializer_class()

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['machine_type', 'driver', 'active']

    ordering_fields = ['name', 'machine_type', 'driver', 'active']

    ordering = ['-active', 'machine_type']

    search_fields = ['name']


class MachineDetail(RetrieveUpdateDestroyAPI):
    """API detail endpoint for MachineConfig object.

    - GET: return a single MachineConfig
    - PUT: update a MachineConfig
    - PATCH: partial update a MachineConfig
    - DELETE: delete a MachineConfig
    """

    queryset = MachineConfig.objects.all()
    serializer_class = MachineSerializers.MachineConfigSerializer


def get_machine(machine_pk):
    """Get machine by pk.

    Raises:
        NotFound: If machine is not found

    Returns:
        BaseMachineType: The machine instance in the registry
    """
    machine = registry.get_machine(machine_pk)

    if machine is None:
        raise NotFound(detail=f"Machine '{machine_pk}' not found")

    return machine


class MachineSettingList(APIView):
    """List endpoint for all machine related settings.

    - GET: return all settings for a machine config
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: MachineSerializers.MachineSettingSerializer(many=True)}
    )
    def get(self, request, pk):
        """Return all settings for a machine config."""
        machine = get_machine(pk)

        all_settings = []

        for settings, config_type in machine.setting_types:
            settings_dict = MachineSetting.all_settings(
                settings_definition=settings,
                machine_config=machine.machine_config,
                config_type=config_type,
            )
            all_settings.extend(list(settings_dict.values()))

        results = MachineSerializers.MachineSettingSerializer(
            all_settings, many=True
        ).data
        return Response(results)


class MachineSettingDetail(RetrieveUpdateAPI):
    """Detail endpoint for a machine-specific setting.

    - GET: Get machine setting detail
    - PUT: Update machine setting
    - PATCH: Update machine setting

    (Note that these cannot be created or deleted via API)
    """

    lookup_field = 'key'
    queryset = MachineSetting.objects.all()
    serializer_class = MachineSerializers.MachineSettingSerializer

    def get_object(self):
        """Lookup machine setting object, based on the URL."""
        pk = self.kwargs['pk']
        key = self.kwargs['key']
        config_type = MachineSetting.get_config_type(self.kwargs['config_type'])

        machine = get_machine(pk)

        setting_map = {d: s for s, d in machine.setting_types}
        if key.upper() not in setting_map[config_type]:
            raise NotFound(
                detail=f"Machine '{machine.name}' has no {config_type.name} setting matching '{key.upper()}'"
            )

        return MachineSetting.get_setting_object(
            key, machine_config=machine.machine_config, config_type=config_type
        )


class MachineRestart(APIView):
    """Endpoint for performing a machine restart.

    - POST: restart machine by pk
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={200: MachineSerializers.MachineRestartSerializer()})
    def post(self, request, pk):
        """Restart machine by pk."""
        machine = get_machine(pk)
        registry.restart_machine(machine)

        result = MachineSerializers.MachineRestartSerializer({'ok': True}).data
        return Response(result)


class MachineTypesList(APIView):
    """List API Endpoint for all discovered machine types.

    - GET: List all machine types
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MachineSerializers.MachineTypeSerializer(many=True)})
    def get(self, request):
        """List all machine types."""
        machine_types = list(registry.machine_types.values())
        results = MachineSerializers.MachineTypeSerializer(
            machine_types, many=True
        ).data
        return Response(results)


class MachineDriverList(APIView):
    """List API Endpoint for all discovered machine drivers.

    - GET: List all machine drivers
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: MachineSerializers.MachineDriverSerializer(many=True)}
    )
    def get(self, request):
        """List all machine drivers."""
        drivers = registry.drivers.values()
        if machine_type := request.query_params.get('machine_type', None):
            drivers = filter(lambda d: d.machine_type == machine_type, drivers)

        results = MachineSerializers.MachineDriverSerializer(
            list(drivers), many=True
        ).data
        return Response(results)


class RegistryStatusView(APIView):
    """Status API endpoint for the machine registry.

    - GET: Provide status data for the machine registry
    """

    permission_classes = [permissions.IsAuthenticated]

    serializer_class = MachineSerializers.MachineRegistryStatusSerializer

    @extend_schema(
        responses={200: MachineSerializers.MachineRegistryStatusSerializer()}
    )
    def get(self, request):
        """Provide status data for the machine registry."""
        result = MachineSerializers.MachineRegistryStatusSerializer({
            'registry_errors': [{'message': str(error)} for error in registry.errors]
        }).data

        return Response(result)


machine_api_urls = [
    # machine types
    path('types/', MachineTypesList.as_view(), name='api-machine-types'),
    # machine drivers
    path('drivers/', MachineDriverList.as_view(), name='api-machine-drivers'),
    # registry status
    path('status/', RegistryStatusView.as_view(), name='api-machine-registry-status'),
    # detail views for a single Machine
    path(
        '<uuid:pk>/',
        include([
            # settings
            path(
                'settings/',
                include([
                    re_path(
                        r'^(?P<config_type>M|D)/(?P<key>\w+)/',
                        MachineSettingDetail.as_view(),
                        name='api-machine-settings-detail',
                    ),
                    path('', MachineSettingList.as_view(), name='api-machine-settings'),
                ]),
            ),
            # restart
            path('restart/', MachineRestart.as_view(), name='api-machine-restart'),
            # detail
            path('', MachineDetail.as_view(), name='api-machine-detail'),
        ]),
    ),
    # machine list and create
    path('', MachineList.as_view(), name='api-machine-list'),
]
