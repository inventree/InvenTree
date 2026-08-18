import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import { TableStatusRenderer } from '../../components/render/StatusRenderer';
import {
  CreationDateColumn,
  DescriptionColumn,
  PartColumn,
  ReferenceColumn,
  ResponsibleColumn,
  StatusColumn,
  TargetDateColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { ncrDispositionStatusType } from '../../defaults/backendMappings';
import { useNonConformanceFields } from '../../forms/NCRForms';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import NonConformanceFilters from './NonConformanceFilters';

export function NonConformanceTable({
  partId
}: Readonly<{
  partId?: number;
}>) {
  const user = useUserState();

  const table = useTable(!!partId ? 'ncr-part' : 'ncr-index');

  const tableFilters = useMemo(() => NonConformanceFilters(), []);

  const tableColumns = useMemo(() => {
    return [
      ReferenceColumn({}),
      PartColumn({}),
      DescriptionColumn({
        accessor: 'title'
      }),
      StatusColumn({ model: ModelType.nonconformance }),
      {
        accessor: 'disposition',
        title: t`Disposition`,
        sortable: true,
        switchable: true,
        minWidth: '50px',
        // 'disposition' is a second, independent status-code field on the same model -
        // there's no separate ModelType for it, so it can't use the StatusColumn helper
        // (which is hardcoded to the 'status'/'status_custom_key' field names)
        render: TableStatusRenderer(
          ncrDispositionStatusType as ModelType,
          'disposition'
        )
      },
      TargetDateColumn({}),
      CreationDateColumn({
        defaultVisible: false
      }),
      ResponsibleColumn({})
    ];
  }, []);

  const ncrFields = useNonConformanceFields({ partId });

  const newNcr = useCreateApiFormModal({
    url: ApiEndpoints.ncr_list,
    title: t`Report Non-Conformance`,
    fields: ncrFields,
    initialData: {
      part: partId
    },
    follow: true,
    modelType: ModelType.nonconformance
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-ncr'
        tooltip={t`Report Non-Conformance`}
        onClick={() => newNcr.open()}
        hidden={!user.hasAddRole(UserRoles.ncr)}
      />
    ];
  }, [user]);

  return (
    <>
      {newNcr.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.ncr_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          params: {
            part: partId,
            part_detail: true
          },
          tableFilters: tableFilters,
          tableActions: tableActions,
          modelType: ModelType.nonconformance,
          enableSelection: true,
          enableDownload: true
        }}
      />
    </>
  );
}
