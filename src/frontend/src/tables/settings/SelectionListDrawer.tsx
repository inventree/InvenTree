import { t } from '@lingui/core/macro';
import { Accordion, LoadingOverlay, Stack } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { EditApiForm } from '../../components/forms/ApiForm';
import {
  selectionEntryFields,
  selectionListFields
} from '../../forms/CommonForms';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

function SelectionListEntriesTable({
  id,
  locked
}: Readonly<{ id: string; locked: boolean }>) {
  const table = useTable('selectionlist-entries');

  const columns: TableColumn[] = useMemo(
    () => [
      { accessor: 'value', sortable: true },
      { accessor: 'label', sortable: true },
      DescriptionColumn({}),
      BooleanColumn({ accessor: 'active' })
    ],
    []
  );

  const entryFields: ApiFormFieldSet = selectionEntryFields();

  const [selectedEntry, setSelectedEntry] = useState<number | undefined>(
    undefined
  );

  const editEntry = useEditApiFormModal({
    url: ApiEndpoints.selectionentry_list,
    pk: selectedEntry,
    pathParams: { id },
    title: t`Edit Selection Entry`,
    fields: entryFields,
    table: table
  });

  const deleteEntry = useDeleteApiFormModal({
    url: ApiEndpoints.selectionentry_list,
    pk: selectedEntry,
    pathParams: { id },
    title: t`Delete Selection Entry`,
    table: table
  });

  const rowActions = useCallback(
    (record: any) => {
      if (locked) {
        return [];
      }

      return [
        RowEditAction({
          onClick: () => {
            setSelectedEntry(record.pk);
            editEntry.open();
          }
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedEntry(record.pk);
            deleteEntry.open();
          }
        })
      ];
    },
    [editEntry, deleteEntry, locked]
  );

  return (
    <>
      {editEntry.modal}
      {deleteEntry.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.selectionentry_list, undefined, { id })}
        tableState={table}
        columns={columns}
        props={{
          enableSearch: true,
          enableSelection: !locked,
          enableBulkDelete: !locked,
          rowActions: locked ? undefined : rowActions
        }}
      />
    </>
  );
}

export default function SelectionListDrawer({
  id,
  refreshTable
}: Readonly<{
  id: string;
  refreshTable: () => void;
}>) {
  const {
    refreshInstance,
    instanceQuery: { isFetching }
  } = useInstance({
    endpoint: ApiEndpoints.selectionlist_list,
    pk: id
  });

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
            <SelectionListEntriesTable id={id} />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
