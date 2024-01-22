import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { ApiPaths } from '../../../enums/ApiEndpoints';
import { useTable } from '../../../hooks/UseTable';
import { apiUrl } from '../../../states/ApiState';
import { TableColumn } from '../Column';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { InvenTreeTableProps } from '../InvenTreeTable';

export default function PartTestTemplateTable({ params }: { params: any }) {
  const table = useTable('part-test-template');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'test_name',
        title: t`Test Name`,
        switchable: false,
        sortable: true
      },
      DescriptionColumn(),
      BooleanColumn({
        accessor: 'required',
        title: t`Required`
      }),
      BooleanColumn({
        accessor: 'requires_value',
        title: t`Requires Value`
      }),
      BooleanColumn({
        accessor: 'requires_attachment',
        title: t`Requires Attachment`
      })
    ];
  }, [params]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'required',
        label: t`Required`,
        description: t`Show required tests`
      },
      {
        name: 'requires_value',
        label: t`Requires Value`,
        description: t`Show tests that require a value`
      },
      {
        name: 'requires_attachment',
        label: t`Requires Attachment`,
        description: t`Show tests that require an attachment`
      }
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiPaths.part_test_template_list)}
      tableState={table}
      columns={tableColumns}
      props={{
        params: {
          ...params
        },
        customFilters: tableFilters
      }}
    />
  );
}
