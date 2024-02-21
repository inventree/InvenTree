import { Trans, t } from '@lingui/macro';
import { Box, Group, LoadingOverlay, Stack, Text, Title } from '@mantine/core';
import { IconDots } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { TemplateEditor } from '../../components/editors/TemplateEditor';
import { CodeEditor } from '../../components/editors/TemplateEditor/CodeEditor';
import { PreviewArea } from '../../components/editors/TemplateEditor/PDFPreview';
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
import { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { RowAction, RowDeleteAction, RowEditAction } from '../RowActions';

export type TemplateI<T extends string> = {
  pk: number;
  name: string;
  description: string;
  filters: string;
  enabled: boolean;
} & { [templateKey in T]: string };

export interface TemplateProps<T> {
  apiEndpoint: ApiEndpoints;
  templateType: 'label' | 'report';
  templateTypeTranslation: string;
  variant: string;
  templateKey: T;
  preview: { itemKey: string; model: ModelType; apiUrl: ApiEndpoints };
}

export function TemplateDrawer<T extends string>({
  id,
  refreshTable,
  templateProps
}: {
  id: string;
  refreshTable: () => void;
  templateProps: TemplateProps<T>;
}) {
  const { apiEndpoint, templateType, templateTypeTranslation, variant } =
    templateProps;
  const navigate = useNavigate();
  const {
    instance: template,
    refreshInstance,
    instanceQuery: { isFetching, error }
  } = useInstance<TemplateI<T>>({
    endpoint: apiEndpoint,
    pathParams: { variant },
    pk: id,
    throwError: true
  });

  const editTemplate = useEditApiFormModal({
    url: apiEndpoint,
    pathParams: { variant },
    pk: id,
    title: t`Edit` + ' ' + templateTypeTranslation,
    fields: {
      name: {},
      description: {},
      filters: {},
      enabled: {}
    },
    onFormSuccess: (data) => {
      refreshInstance();
      refreshTable();
    }
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: apiEndpoint,
    pathParams: { variant },
    pk: id,
    title: t`Delete` + ' ' + templateTypeTranslation,
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
          <Trans>
            {templateTypeTranslation} with id {id} not found
          </Trans>
        ) : (
          <Trans>
            An error occurred while fetching {templateTypeTranslation} details
          </Trans>
        )}
      </Text>
    );
  }

  return (
    <Stack spacing="xs">
      {editTemplate.modal}
      {deleteTemplate.modal}

      <Group position="apart">
        <Box></Box>

        <Group>
          <Title order={4}>{template?.name}</Title>
        </Group>

        <Group>
          <ActionDropdown
            tooltip={templateTypeTranslation + ' ' + t`actions`}
            icon={<IconDots />}
            actions={[
              EditItemAction({
                tooltip: t`Edit` + ' ' + templateTypeTranslation,
                onClick: editTemplate.open
              }),
              DeleteItemAction({
                tooltip: t`Delete` + ' ' + templateTypeTranslation,
                onClick: deleteTemplate.open
              })
            ]}
          />
        </Group>
      </Group>

      <TemplateEditor
        downloadUrl={template[templateProps.templateKey as keyof TemplateI<T>]}
        uploadUrl={apiUrl(apiEndpoint, id, { variant })}
        uploadKey={templateProps.templateKey}
        preview={templateProps.preview}
        templateType={templateType}
        codeEditors={[
          {
            key: 'code',
            name: t`Code`,
            component: CodeEditor
          }
        ]}
        previewAreas={[
          {
            key: 'pdf-preview',
            name: t`PDF Preview`,
            component: PreviewArea
          }
        ]}
      />
    </Stack>
  );
}

export function TemplateTable<T extends string>({
  templateProps
}: {
  templateProps: TemplateProps<T>;
}) {
  const {
    apiEndpoint,
    templateType,
    templateTypeTranslation,
    variant,
    templateKey
  } = templateProps;
  const table = useTable(`${templateType}-${variant}`);
  const navigate = useNavigate();

  const openDetailDrawer = useCallback((pk: number) => navigate(`${pk}/`), []);

  const columns: TableColumn<TemplateI<T>>[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`
      },
      {
        accessor: 'description',
        sortable: false,
        title: t`Description`
      },
      {
        accessor: 'filters',
        sortable: false,
        title: t`Filters`
      },
      BooleanColumn({ accessor: 'enabled', title: t`Enabled` })
    ];
  }, []);

  const [selectedTemplate, setSelectedTemplate] = useState<number>(-1);

  const rowActions = useCallback((record: TemplateI<T>): RowAction[] => {
    return [
      RowEditAction({
        onClick: () => openDetailDrawer(record.pk)
      }),
      RowDeleteAction({
        onClick: () => {
          setSelectedTemplate(record.pk), deleteTemplate.open();
        }
      })
    ];
  }, []);

  const deleteTemplate = useDeleteApiFormModal({
    url: apiEndpoint,
    pathParams: { variant },
    pk: selectedTemplate,
    title: t`Delete` + ' ' + templateTypeTranslation,
    onFormSuccess: table.refreshTable
  });

  const newTemplate = useCreateApiFormModal({
    url: apiEndpoint,
    pathParams: { variant },
    title: t`Create new` + ' ' + templateTypeTranslation,
    fields: {
      name: {},
      description: {},
      filters: {},
      enabled: {},
      [templateKey]: {
        hidden: true,
        value: new File(['<html></html>'], 'template.html')
      }
    },
    onFormSuccess: (data) => {
      table.refreshTable();
      openDetailDrawer(data.pk);
    }
  });

  const tableActions = useMemo(() => {
    let actions = [];

    actions.push(
      <AddItemButton
        key={`add-${templateType}`}
        onClick={() => newTemplate.open()}
        tooltip={t`Add` + ' ' + templateTypeTranslation}
      />
    );

    return actions;
  }, []);

  return (
    <>
      {newTemplate.modal}
      {deleteTemplate.modal}
      <DetailDrawer
        title={t`Edit` + ' ' + templateTypeTranslation}
        size={'90%'}
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
        url={apiUrl(apiEndpoint, undefined, { variant })}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          onRowClick: (record) => openDetailDrawer(record.pk)
        }}
      />
    </>
  );
}
