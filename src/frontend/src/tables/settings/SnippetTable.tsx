import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { DetailDrawer } from '@lib/components/nav/DetailDrawer';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Group,
  LoadingOverlay,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconFileCode, IconInfoCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CodeEditor,
  TemplateEditor
} from '../../components/editors/TemplateEditor';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { DescriptionColumn } from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserState } from '../../states/UserState';
import type { TemplateI } from './TemplateTable';

export type SnippetI = {
  pk: number;
  snippet: string;
  description: string;
};

export function SnippetDrawer({
  id
}: Readonly<{
  id: string | number;
}>) {
  const {
    instance: snippet,
    instanceQuery: { isFetching, error }
  } = useInstance<SnippetI>({
    endpoint: ApiEndpoints.report_snippet,
    hasPrimaryKey: true,
    pk: id
  });

  const filename = useMemo(
    () => snippet?.snippet?.split('/').pop() ?? '',
    [snippet]
  );

  if (isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (error || !snippet) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>Snippet not found</Trans>
        ) : (
          <Trans>An error occurred while fetching snippet details</Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack gap='xs' style={{ display: 'flex', flex: '1' }}>
      <Group justify='left'>
        <Title order={4}>{filename}</Title>
      </Group>

      <TemplateEditor
        templateUrl={apiUrl(ApiEndpoints.report_snippet, id)}
        template={snippet as unknown as TemplateI}
        fileField='snippet'
        editors={[CodeEditor]}
        previewAreas={[]}
      />
    </Stack>
  );
}

export default function SnippetTable() {
  const table = useTable('report-snippet');
  const navigate = useNavigate();
  const user = useUserState();

  const openDetailDrawer = useCallback((pk: number) => navigate(`${pk}/`), []);

  const columns: TableColumn<SnippetI>[] = useMemo(() => {
    return [
      {
        accessor: 'snippet',
        title: t`Snippet`,
        sortable: false,
        switchable: false,
        render: (record: SnippetI) => {
          if (!record.snippet) {
            return '-';
          }

          return <AttachmentLink attachment={record.snippet} />;
        },
        noContext: true
      },
      DescriptionColumn({
        accessor: 'description',
        sortable: false,
        switchable: false
      })
    ];
  }, []);

  const [selectedSnippet, setSelectedSnippet] = useState<number>(-1);

  const rowActions = useCallback(
    (record: SnippetI): RowAction[] => {
      return [
        {
          title: t`Modify`,
          tooltip: t`Modify snippet file`,
          icon: <IconFileCode />,
          onClick: () => openDetailDrawer(record.pk),
          hidden: !user.isStaff()
        },
        RowEditAction({
          hidden: !user.isStaff(),
          onClick: () => {
            setSelectedSnippet(record.pk);
            editSnippet.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.isStaff(),
          onClick: () => {
            setSelectedSnippet(record.pk);
            deleteSnippet.open();
          }
        })
      ];
    },
    [user]
  );

  const editSnippetFields: ApiFormFieldSet = useMemo(() => {
    return {
      description: {}
    };
  }, []);

  const newSnippetFields: ApiFormFieldSet = useMemo(() => {
    return {
      snippet: {},
      description: {}
    };
  }, []);

  const editSnippet = useEditApiFormModal({
    url: ApiEndpoints.report_snippet,
    pk: selectedSnippet,
    title: t`Edit Snippet`,
    fields: editSnippetFields,
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const deleteSnippet = useDeleteApiFormModal({
    url: ApiEndpoints.report_snippet,
    pk: selectedSnippet,
    title: t`Delete Snippet`,
    table: table
  });

  const newSnippet = useCreateApiFormModal({
    url: ApiEndpoints.report_snippet,
    title: t`Add Snippet`,
    fields: newSnippetFields,
    onFormSuccess: (data) => {
      table.refreshTable();
      openDetailDrawer(data.pk);
    }
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        key='add-snippet'
        onClick={() => newSnippet.open()}
        tooltip={t`Add snippet`}
        hidden={!user.isStaff()}
      />
    ];
  }, [user]);

  return (
    <>
      {newSnippet.modal}
      {editSnippet.modal}
      {deleteSnippet.modal}
      <DetailDrawer
        title={t`Edit Snippet`}
        size={'90%'}
        closeOnEscape={false}
        renderContent={(id) => {
          return <SnippetDrawer id={id ?? ''} />;
        }}
      />
      <Alert icon={<IconInfoCircle />} title={t`Snippets`}>
        <Text>{t`Snippets are reusable pieces of HTML content that can be inserted into reports and labels.`}</Text>
      </Alert>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.report_snippet)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          enableSearch: false,
          enableFilters: false,
          onRowClick: (record) => openDetailDrawer(record.pk)
        }}
      />
    </>
  );
}
