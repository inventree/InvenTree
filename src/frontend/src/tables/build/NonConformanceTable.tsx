import { t } from '@lingui/core/macro';
import { useMemo } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
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
      DescriptionColumn({}),
      StatusColumn({ model: ModelType.nonconformance }),
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
          enableReports: true,
          enableDownload: true
        }}
      />
    </>
  );
}
