import { Trans, t } from '@lingui/macro';
import { Box, Group, LoadingOverlay, Stack, Text, Title } from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import { ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import {
  CodeEditor,
  PdfPreview,
  TemplateEditor
} from '../../components/editors/TemplateEditor';
import { TemplatePreviewProps } from '../../components/editors/TemplateEditor/TemplateEditor';
import { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import {
  ActionDropdown,
  DeleteItemAction,
  EditItemAction
} from '../../components/items/ActionDropdown';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';

export type TemplateI = {
  pk: number;
  name: string;
  description: string;
  filters: string;
  enabled: boolean;
};

export interface TemplateProps {
  apiEndpoint: ApiEndpoints;
  templateType: 'label' | 'report';
  additionalFormFields?: ApiFormFieldSet;
}

export function TemplateDrawer({
  id,
  refreshTable,
  templateProps
}: {
  id: string;
  refreshTable: () => void;
  templateProps: TemplateProps;
}) {
  const { apiEndpoint, templateType, additionalFormFields } = templateProps;
  const navigate = useNavigate();
  const {
    instance: template,
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance<TemplateI>({
    endpoint: apiEndpoint,
    pk: id,
    throwError: true
  });

  const editTemplate = useEditApiFormModal({
    url: apiEndpoint,
    pk: id,
    title: t`Edit Template`,
    fields: {
      name: {},
      description: {},
      filters: {},
      enabled: {},
      ...additionalFormFields
    },
    onFormSuccess: (data) => {
      refreshInstance();
      refreshTable();
    }
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: apiEndpoint,
    pk: id,
    title: t`Delete Template`,
    onFormSuccess: () => {
      refreshTable();
      navigate('../');
    }
  });

  if (isFetching) {
    return <LoadingOverlay visible={true} />;
  }

  if (error || !template) {
    return (
      <Text>
        {(error as any)?.response?.status === 404 ? (
          <Trans>Template not found</Trans>
        ) : (
          <Trans>An error occurred while fetching template details</Trans>
        )}
      </Text>
    );
  }

  const previewProps: TemplatePreviewProps = useMemo(() => {
    return {
      itemKey: 'item',
      model: ModelType.stockitem
    };
  }, []);

  return (
    <Stack spacing="xs" style={{ display: 'flex', flex: '1' }}>
      {editTemplate.modal}
      {deleteTemplate.modal}

      <Group position="apart">
        <Box></Box>

        <Group>
          <Title order={4}>{template?.name}</Title>
        </Group>

        <Group>
          <ActionDropdown
            tooltip={t`Template actions`}
            icon={<IconDots />}
            actions={[
              EditItemAction({
                tooltip: t`Edit template`,
                onClick: editTemplate.open
              }),
              DeleteItemAction({
                tooltip: t`Delete template`,
                onClick: deleteTemplate.open
              })
            ]}
          />
        </Group>
      </Group>

      <TemplateEditor
        url={apiUrl(apiEndpoint, id)}
        preview={previewProps}
        templateType={templateType}
        template={template}
        editors={[CodeEditor]}
        previewAreas={[PdfPreview]}
      />
    </Stack>
  );
}

export function TemplateTable({
  templateProps
}: {
  templateProps: TemplateProps;
}) {
  const { apiEndpoint, templateType, additionalFormFields } = templateProps;

  const table = useTable(`${templateType}-template`);
  const navigate = useNavigate();
  const user = useUserState();

  const openDetailDrawer = useCallback((pk: number) => navigate(`${pk}/`), []);

  const columns: TableColumn<TemplateI>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'description',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'model_type',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'filters',
        sortable: false,
        switchable: true
      },
      ...Object.entries(additionalFormFields || {})?.map(([key, field]) => ({
        accessor: key,
        sortable: false
      })),
      BooleanColumn({ accessor: 'enabled', title: t`Enabled` })
    ];
  }, [additionalFormFields]);

  const [selectedTemplate, setSelectedTemplate] = useState<number>(-1);

  const rowActions = useCallback(
    (record: TemplateI): RowAction[] => {
      return [
        RowEditAction({
          onClick: () => openDetailDrawer(record.pk)
        }),
        RowDuplicateAction({
          // TODO: Duplicate selected template
        }),
        RowDeleteAction({
          onClick: () => {
            setSelectedTemplate(record.pk), deleteTemplate.open();
          }
        })
      ];
    },
    [user]
  );

  const deleteTemplate = useDeleteApiFormModal({
    url: apiEndpoint,
    pk: selectedTemplate,
    title: t`Delete template`,
    onFormSuccess: table.refreshTable
  });

  const newTemplate = useCreateApiFormModal({
    url: apiEndpoint,
    title: t`Add Template`,
    fields: {
      name: {},
      description: {},
      model_type: {},
      template: {},
      filters: {},
      filename_pattern: {},
      enabled: {},
      ...additionalFormFields
    },
    onFormSuccess: (data) => {
      table.refreshTable();
      openDetailDrawer(data.pk);
    }
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        key={`add-${templateType}`}
        onClick={() => newTemplate.open()}
        tooltip={t`Add template`}
      />
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Filter by enabled status`,
        type: 'checkbox'
      }
      // TODO: Implement "model_type" filter
      // TODO: This will require a lookup of the available model types (via OPTIONS API)
    ];
  }, []);

  return (
    <>
      {newTemplate.modal}
      {deleteTemplate.modal}
      <DetailDrawer
        title={t`Edit Template`}
        size={'90%'}
        closeOnEscape={false}
        renderContent={(id) => {
          return (
            <TemplateDrawer
              id={id ?? ''}
              refreshTable={table.refreshTable}
              templateProps={templateProps}
            />
          );
        }}
      />
      <InvenTreeTable
        url={apiUrl(apiEndpoint)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableFilters: tableFilters,
          tableActions: tableActions,
          onRowClick: (record) => openDetailDrawer(record.pk)
        }}
      />
    </>
  );
}
