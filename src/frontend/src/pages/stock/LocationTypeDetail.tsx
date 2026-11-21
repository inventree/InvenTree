import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { getDetailUrl, getOverviewUrl } from '@lib/functions/Navigation';
import type { PanelType } from '@lib/types/Panel';
import { t } from '@lingui/core/macro';
import { Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AdminButton from '../../components/buttons/AdminButton';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { getStockLocationTypeFields } from '../../forms/StockForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import { LocationTypeDetailsPanel } from './LocationTypeDetailsPanel';

export default function LocationTypeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isStaff = useUserState((state) => state.isStaff());
  const canEdit = useUserState((state) =>
    state.hasChangePermission(ModelType.stocklocationtype)
  );
  const canDelete = useUserState((state) =>
    state.hasDeletePermission(ModelType.stocklocationtype)
  );
  const stockOverviewUrl = getOverviewUrl(ModelType.stocklocation);
  const locationTypesUrl = '/settings/admin/location-types';
  const {
    instance: locationType,
    instanceQuery,
    refreshInstance
  } = useInstance({
    endpoint: ApiEndpoints.stock_location_type_list,
    pk: id
  });

  const editLocationType = useEditApiFormModal({
    url: ApiEndpoints.stock_location_type_list,
    pk: id,
    title: t`Edit Location Type`,
    fields: useMemo(getStockLocationTypeFields, []),
    onFormSuccess: refreshInstance
  });

  const deleteLocationType = useDeleteApiFormModal({
    url: ApiEndpoints.stock_location_type_list,
    pk: id,
    title: t`Delete Location Type`,
    onFormSuccess: () =>
      navigate(isStaff ? locationTypesUrl : stockOverviewUrl, { replace: true })
  });

  const panels = useMemo<PanelType[]>(
    () => [
      {
        name: 'details',
        label: t`Details`,
        icon: <IconInfoCircle />,
        content: <LocationTypeDetailsPanel instance={locationType} />
      }
    ],
    [locationType]
  );

  return (
    <InstanceDetail
      query={instanceQuery}
      requiredPermission={ModelType.stocklocationtype}
    >
      {editLocationType.modal}
      {deleteLocationType.modal}
      <Stack gap='xs'>
        <PageDetail
          model={ModelType.stocklocationtype}
          id={locationType.pk}
          title={locationType.name}
          subtitle={t`Stock Location Type`}
          icon={locationType.icon && <ApiIcon name={locationType.icon} />}
          editAction={editLocationType.open}
          editEnabled={canEdit}
          actions={[
            <AdminButton
              key='admin'
              model={ModelType.stocklocationtype}
              id={locationType.pk}
            />,
            <OptionsActionDropdown
              key='location-type-actions'
              tooltip={t`Location Type Actions`}
              actions={[
                ...(canEdit
                  ? [EditItemAction({ onClick: editLocationType.open })]
                  : []),
                ...(canDelete
                  ? [DeleteItemAction({ onClick: deleteLocationType.open })]
                  : [])
              ]}
            />
          ]}
          breadcrumbs={[
            { name: t`Stock`, url: stockOverviewUrl },
            ...(isStaff
              ? [
                  {
                    name: t`Location Types`,
                    url: locationTypesUrl
                  }
                ]
              : [])
          ]}
          lastCrumb={[
            {
              name: locationType.name,
              url: getDetailUrl(ModelType.stocklocationtype, locationType.pk)
            }
          ]}
        />
        <PanelGroup
          pageKey='stocklocationtype'
          panels={panels}
          model={ModelType.stocklocationtype}
          id={locationType.pk}
          instance={locationType}
          reloadInstance={refreshInstance}
        />
      </Stack>
    </InstanceDetail>
  );
}
