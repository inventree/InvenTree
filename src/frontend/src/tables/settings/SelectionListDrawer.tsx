import { t } from '@lingui/core/macro';
import { Accordion, Alert, LoadingOverlay, Stack } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { IconLock } from '@tabler/icons-react';
import { EditApiForm } from '../../components/forms/ApiForm';
import {
  BooleanColumn,
  DescriptionColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import {
  selectionEntryFields,
  selectionListFields
} from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';

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

  // Construct the dynamic URL to edit (or delete) the selected entry
  const selectedEntryUrl: string = useMemo(() => {
    let url = apiUrl(ApiEndpoints.selectionentry_list, undefined, { id });

    if (selectedEntry) {
      url += `${selectedEntry}/`;
    }

    return url;
  }, [id, selectedEntry]);

  const createEntry = useCreateApiFormModal({
    url: ApiEndpoints.selectionentry_list,
    pathParams: { id },
    title: t`Add Selection Entry`,
    fields: {
      ...entryFields,
      list: {
        value: id,
        hidden: true
      }
    },
    table: table
  });

  const editEntry = useEditApiFormModal({
    url: selectedEntryUrl,
    title: t`Edit Selection Entry`,
    fields: entryFields,
    table: table
  });

  const deleteEntry = useDeleteApiFormModal({
    url: selectedEntryUrl,
    title: t`Delete Selection Entry`,
    table: table
  });

  const tableActions = useMemo(() => {
    if (locked) return [];
    return [
      <AddItemButton
        key='add-entry'
        onClick={() => createEntry.open()}
        tooltip={t`Add Entry`}
      />
    ];
  }, [locked, createEntry]);

  const rowActions = useCallback(
    (record: any) => {
      if (locked) {
        return [];
      }

      return [
        RowEditAction({
          onClick: () => {
            setSelectedEntry(record.id);
            editEntry.open();
          }
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedEntry(record.id);
            deleteEntry.open();
          }
        })
      ];
    },
    [editEntry, deleteEntry, locked]
  );

  return (
    <>
      {createEntry.modal}
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
          tableActions: tableActions,
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
    instance,
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
      {instance.locked && (
        <Alert color='red' icon={<IconLock />} title={t`Locked`}>
          {t`This selection list is locked and cannot be edited.`}
        </Alert>
      )}
      <Accordion defaultValue={['details', 'entries']} multiple>
        <Accordion.Item key='details' value='details'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Selection List Details`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <fieldset
              disabled={instance.locked}
              style={{ border: 'none', padding: 0, margin: 0 }}
            >
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
            </fieldset>
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item key='entries' value='entries'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Selection List Entries`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <SelectionListEntriesTable
              id={id}
              locked={instance?.locked ?? false}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
