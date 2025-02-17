import { t } from '@lingui/macro';
import { Accordion, Stack } from '@mantine/core';
import { useMemo } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { useTable } from '../../../../hooks/UseTable';
import { apiUrl } from '../../../../states/ApiState';
import { BooleanColumn } from '../../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../../tables/InvenTreeTable';
import CustomUnitsTable from '../../../../tables/settings/CustomUnitsTable';

function AllUnitTable() {
  const table = useTable('all-units', 'name');
  const columns = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`
      },
      BooleanColumn({ accessor: 'is_alias', title: t`Alias` }),
      BooleanColumn({ accessor: 'isdimensionless', title: t`Dimensionless` })
    ];
  }, []);

  return (
    <InvenTreeTable
      url={apiUrl(ApiEndpoints.all_units)}
      tableState={table}
      columns={columns}
      props={{
        enableSearch: false,
        enablePagination: false,
        enableColumnSwitching: false,
        dataFormatter: (data: any) => {
          const units = data.available_units ?? {};
          return Object.entries(units).map(([key, values]: [string, any]) => {
            return {
              name: values.name,
              is_alias: values.is_alias,
              compatible_units: values.compatible_units,
              isdimensionless: values.isdimensionless
            };
          });
        }
      }}
    />
  );
}

export default function UnitManagementPanel() {
  return (
    <Stack gap='xs'>
      <Accordion defaultValue='custom'>
        <Accordion.Item value='custom' key='custom'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Custom Units`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <CustomUnitsTable />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='all' key='all'>
          <Accordion.Control>
            <StylishText size='lg'>{t`All units`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <AllUnitTable />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
