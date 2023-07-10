from django.urls import include, path, re_path

from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

import machine.serializers as MachineSerializers
from generic.states.api import StatusView
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (ListCreateAPI, RetrieveUpdateAPI,
                              RetrieveUpdateDestroyAPI)
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
        # allow driver, machine_type fields on creation
        if self.request.method == "POST":
            return MachineSerializers.MachineConfigCreateSerializer
        return super().get_serializer_class()

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = [
        "machine_type",
        "driver",
        "active",
    ]

    ordering_fields = [
        "name",
        "machine_type",
        "driver",
        "active",
    ]

    ordering = [
        "-active",
        "machine_type",
    ]

    search_fields = [
        "name"
    ]


class MachineDetail(RetrieveUpdateDestroyAPI):
    """API detail endpoint for MachineConfig object.

    - GET: return a single MachineConfig
    - PUT: update a MachineConfig
    - PATCH: partial update a MachineConfig
    - DELETE: delete a MachineConfig
    """

    queryset = MachineConfig.objects.all()
    serializer_class = MachineSerializers.MachineConfigSerializer

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


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

    @extend_schema(responses={200: MachineSerializers.MachineSettingSerializer(many=True)})
    def get(self, request, pk):
        machine = get_machine(pk)

        setting_types = [
            (machine.machine_settings, MachineSetting.ConfigType.MACHINE),
            (machine.driver_settings, MachineSetting.ConfigType.DRIVER),
        ]

        all_settings = []

        for settings, config_type in setting_types:
            all_settings.extend(MachineSetting.all_items(settings, machine_config=machine.machine_config, config_type=config_type))

        results = MachineSerializers.MachineSettingSerializer(all_settings, many=True).data
        return Response(results)


class MachineSettingDetail(RetrieveUpdateAPI):
    """Detail endpoint for a machine-specific setting.

    - GET: Get machine setting detail
    - PUT: Update machine setting
    - PATCH: Update machine setting

    (Note that these cannot be created or deleted via API)
    """

    queryset = MachineSetting.objects.all()
    serializer_class = MachineSerializers.MachineSettingSerializer

    def get_object(self):
        """Lookup machine setting object, based on the URL."""
        pk = self.kwargs["pk"]
        key = self.kwargs["key"]
        config_type = MachineSetting.get_config_type(self.kwargs["config_type"])

        machine = get_machine(pk)

        setting_map = {MachineSetting.ConfigType.MACHINE: machine.machine_settings,
                       MachineSetting.ConfigType.DRIVER: machine.driver_settings}
        if key.upper() not in setting_map[config_type]:
            raise NotFound(detail=f"Machine '{machine.name}' has no {config_type.name} setting matching '{key.upper()}'")

        return MachineSetting.get_setting_object(key, machine_config=machine.machine_config, config_type=config_type)


class MachineTypesList(APIView):
    """List API Endpoint for all discovered machine types.

    - GET: List all machine types
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MachineSerializers.MachineTypeSerializer(many=True)})
    def get(self, request):
        machine_types = list(registry.machine_types.values())
        results = MachineSerializers.MachineTypeSerializer(machine_types, many=True).data
        return Response(results)


class MachineTypeStatusView(StatusView):
    """List all status codes for a machine type.

    - GET: List all status codes for this machine type
    """

    def get_status_model(self, *args, **kwargs):
        # dynamically inject the StatusCode model from the machine type url param
        machine_type = registry.machine_types.get(self.kwargs["machine_type"], None)
        if machine_type is None:
            raise NotFound(detail=f"Machine type '{self.kwargs['machine_type']}' not found")
        self.kwargs[self.MODEL_REF] = machine_type.MACHINE_STATUS
        return super().get_status_model(*args, **kwargs)


class MachineDriverList(APIView):
    """List API Endpoint for all discovered machine drivers.

    - GET: List all machine drivers
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MachineSerializers.MachineDriverSerializer(many=True)})
    def get(self, request):
        drivers = registry.drivers.values()
        if machine_type := request.query_params.get("machine_type", None):
            drivers = filter(lambda d: d.machine_type == machine_type, drivers)

        results = MachineSerializers.MachineDriverSerializer(list(drivers), many=True).data
        return Response(results)


class RegistryStatusView(APIView):
    """Status API endpoint for the machine registry.

    - GET: Provide status data for the machine registry
    """

    permission_classes = [permissions.IsAuthenticated]

    serializer_class = MachineSerializers.MachineRegistryStatusSerializer

    def get(self, request):
        result = MachineSerializers.MachineRegistryStatusSerializer({
            "registry_errors": list(map(str, registry.errors))
        }).data

        return Response(result)


machine_api_urls = [
    # machine types
    re_path(r"^types/", include([
        path(r"<slug:machine_type>/", include([
            re_path(r"^status/", MachineTypeStatusView.as_view(), name="api-machine-type-status"),
        ])),
        re_path(r"^.*$", MachineTypesList.as_view(), name="api-machine-types"),
    ])),

    # machine drivers
    re_path(r"^drivers/", MachineDriverList.as_view(), name="api-machine-drivers"),

    # registry status
    re_path(r"^status/", RegistryStatusView.as_view(), name="api-machine-registry-status"),

    # detail views for a single Machine
    path(r"<uuid:pk>/", include([
        re_path(r"^settings/", include([
            re_path(r"^(?P<config_type>M|D)/(?P<key>\w+)/", MachineSettingDetail.as_view(), name="api-machine-settings-detail"),
            re_path(r"^.*$", MachineSettingList.as_view(), name="api-machine-settings"),
        ])),

        re_path(r"^.*$", MachineDetail.as_view(), name="api-machine-detail"),
    ])),

    # machine list and create
    re_path(r"^.*$", MachineList.as_view(), name="api-machine-list"),
]
