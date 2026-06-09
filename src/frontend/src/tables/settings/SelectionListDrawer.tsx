import { t } from '@lingui/core/macro';
import { Accordion, LoadingOverlay, Stack } from '@mantine/core';
import { useMemo } from 'react';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { EditApiForm } from '../../components/forms/ApiForm';
import { selectionListFields } from '../../forms/CommonForms';
import { useInstance } from '../../hooks/UseInstance';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export default function SelectionListDrawer({
  id,
  refreshTable
}: Readonly<{
  id: string;
  refreshTable: () => void;
}>) {
  const entriesTable = useTable('selectionlist-entries');

  const {
    refreshInstance,
    instanceQuery: { isFetching }
  } = useInstance({
    endpoint: ApiEndpoints.selectionlist_list,
    pk: id
  });

  const entryColumns: TableColumn[] = useMemo(
    () => [
      { accessor: 'value', sortable: true },
      { accessor: 'label', sortable: true },
      DescriptionColumn({}),
      BooleanColumn({ accessor: 'active' })
    ],
    []
  );

  const selectionFields: ApiFormFieldSet = useMemo(() => {
    return selectionListFields();
  }, []);

  if (isFetching) {
    return <LoadingOverlay visible />;
  }

  return (
    <Stack>
      <Accordion defaultValue={['details', 'entries']} multiple>
        <Accordion.Item key='details' value='details'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Selection List Details`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <EditApiForm
              props={{
                url: ApiEndpoints.selectionlist_list,
                pk: id,
                fields: selectionFields,
                onFormSuccess: () => {
                  refreshTable();
                  refreshInstance();
                }
              }}
              id={`selection-list-drawer-${id}`}
            />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item key='entries' value='entries'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Selection List Entries`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <InvenTreeTable
              url={apiUrl(ApiEndpoints.selectionentry_list, undefined, {
                id
              })}
              tableState={entriesTable}
              columns={entryColumns}
              props={{}}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
