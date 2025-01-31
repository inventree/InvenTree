import { Trans, t } from '@lingui/macro';
import { Group, LoadingOverlay, Stack, Text, Title } from '@mantine/core';
import { IconFileCode } from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import {
  CodeEditor,
  PdfPreview,
  TemplateEditor
} from '../../components/editors/TemplateEditor';
import type {
  Editor,
  PreviewArea
} from '../../components/editors/TemplateEditor/TemplateEditor';
import type { ApiFormFieldSet } from '../../components/forms/fields/ApiFormField';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { DetailDrawer } from '../../components/nav/DetailDrawer';
import {
  getPluginTemplateEditor,
  getPluginTemplatePreview
} from '../../components/plugins/PluginUIFeature';
import type {
  TemplateEditorUIFeature,
  TemplatePreviewUIFeature
} from '../../components/plugins/PluginUIFeatureTypes';
import type { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { identifierString } from '../../functions/conversion';
import { GetIcon } from '../../functions/icons';
import { notYetImplemented } from '../../functions/notifications';
import { useFilters } from '../../hooks/UseFilter';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { usePluginUIFeature } from '../../hooks/UsePluginUIFeature';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import { BooleanColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import {
  type RowAction,
  RowDeleteAction,
  RowDuplicateAction,
  RowEditAction
} from '../RowActions';

export type TemplateI = {
  pk: number;
  name: string;
  description: string;
  model_type: ModelType;
  filters: string;
  filename_pattern: string;
  enabled: boolean;
  template: string;
};

export interface TemplateProps {
  modelType: ModelType.labeltemplate | ModelType.reporttemplate;
  templateEndpoint: ApiEndpoints;
  printingEndpoint: ApiEndpoints;
  additionalFormFields?: ApiFormFieldSet;
}

export function TemplateDrawer({
  id,
  templateProps
}: Readonly<{
  id: string | number;
  templateProps: TemplateProps;
}>) {
  const { modelType, templateEndpoint, printingEndpoint } = templateProps;

  const {
    instance: template,
    instanceQuery: { isFetching, error }
  } = useInstance<TemplateI>({
    endpoint: templateEndpoint,
    hasPrimaryKey: true,
    pk: id,
    throwError: true
  });

  // Editors
  const extraEditors = usePluginUIFeature<TemplateEditorUIFeature>({
    enabled: template?.model_type !== undefined,
    featureType: 'template_editor',
    context: { template_type: modelType, template_model: template?.model_type! }
  });

  /**
   * List of available editors for the template
   */
  const editors = useMemo(() => {
    // Always include the built-in code editor
    const editors = [CodeEditor];

    if (!template) {
      return editors;
    }

    editors.push(
      ...(extraEditors?.map((editor) => {
        return {
          key: identifierString(
            `${editor.options.plugin_name}-${editor.options.key}`
          ),
          name: editor.options.title,
          icon: GetIcon(editor.options.icon || 'plugin'),
          component: getPluginTemplateEditor(editor.func, template)
        } as Editor;
      }) || [])
    );

    return editors;
  }, [extraEditors, template]);

  // Previews
  const extraPreviews = usePluginUIFeature<TemplatePreviewUIFeature>({
    enabled: template?.model_type !== undefined,
    featureType: 'template_preview',
    context: { template_type: modelType, template_model: template?.model_type! }
  });
  const previews = useMemo(() => {
    const previews = [PdfPreview];

    if (!template) {
      return previews;
    }

    previews.push(
      ...(extraPreviews?.map(
        (preview) =>
          ({
            key: preview.options.key,
            name: preview.options.title,
            icon: GetIcon(preview.options.icon || 'plugin'),
            component: getPluginTemplatePreview(preview.func, template)
          }) as PreviewArea
      ) || [])
    );

    return previews;
  }, [extraPreviews, template]);

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

  return (
    <Stack gap='xs' style={{ display: 'flex', flex: '1' }}>
      <Group justify='left'>
        <Title order={4}>{template?.name}</Title>
      </Group>

      <TemplateEditor
        templateUrl={apiUrl(templateEndpoint, id)}
        printingUrl={apiUrl(printingEndpoint)}
        template={template}
        editors={editors}
        previewAreas={previews}
      />
    </Stack>
  );
}

export function TemplateTable({
  templateProps
}: Readonly<{
  templateProps: TemplateProps;
}>) {
  const { templateEndpoint, additionalFormFields } = templateProps;

  const table = useTable(`${templateEndpoint}-template`);
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
        accessor: 'template',
        sortable: false,
        switchable: true,
        render: (record: any) => {
          if (!record.template) {
            return '-';
          }

          return <AttachmentLink attachment={record.template} />;
        },
        noContext: true
      },
      {
        accessor: 'model_type',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'revision',
        sortable: false,
        switchable: true
      },
      {
        accessor: 'filters',
        sortable: false,
        switchable: true
      },
      ...Object.entries(additionalFormFields || {}).map(([key, field]) => ({
        accessor: key,
        ...field,
        title: field.label,
        sortable: false,
        switchable: true,
        render: field.modelRenderer
      })),
      BooleanColumn({ accessor: 'enabled', title: t`Enabled` })
    ];
  }, [additionalFormFields]);

  const [selectedTemplate, setSelectedTemplate] = useState<number>(-1);

  const rowActions = useCallback(
    (record: TemplateI): RowAction[] => {
      return [
        {
          title: t`Modify`,
          tooltip: t`Modify template file`,
          icon: <IconFileCode />,
          onClick: () => openDetailDrawer(record.pk),
          hidden: !user.hasChangePermission(templateProps.modelType)
        },
        RowEditAction({
          hidden: !user.hasChangePermission(templateProps.modelType),
          onClick: () => {
            setSelectedTemplate(record.pk);
            editTemplate.open();
          }
        }),
        RowDuplicateAction({
          hidden: true,
          // TODO: Duplicate selected template
          onClick: notYetImplemented
        }),
        RowDeleteAction({
          hidden: !user.hasDeletePermission(templateProps.modelType),
          onClick: () => {
            setSelectedTemplate(record.pk);
            deleteTemplate.open();
          }
        })
      ];
    },
    [user]
  );

  const templateFields: ApiFormFieldSet = {
    name: {},
    description: {},
    model_type: {},
    filters: {},
    filename_pattern: {},
    enabled: {}
  };

  const editTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      ...templateFields,
      ...additionalFormFields
    };
  }, [additionalFormFields]);

  const newTemplateFields: ApiFormFieldSet = useMemo(() => {
    return {
      template: {},
      ...templateFields,
      ...additionalFormFields
    };
  }, [additionalFormFields]);

  const editTemplate = useEditApiFormModal({
    url: templateEndpoint,
    pk: selectedTemplate,
    title: t`Edit Template`,
    fields: editTemplateFields,
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const deleteTemplate = useDeleteApiFormModal({
    url: templateEndpoint,
    pk: selectedTemplate,
    title: t`Delete template`,
    table: table
  });

  const newTemplate = useCreateApiFormModal({
    url: templateEndpoint,
    title: t`Add Template`,
    fields: newTemplateFields,
    onFormSuccess: (data) => {
      table.refreshTable();
      openDetailDrawer(data.pk);
    }
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        key='add-template'
        onClick={() => newTemplate.open()}
        tooltip={t`Add template`}
        hidden={!user.hasAddPermission(templateProps.modelType)}
      />
    ];
  }, [user]);

  const modelTypeFilters = useFilters({
    url: apiUrl(templateEndpoint),
    method: 'OPTIONS',
    accessor: 'data.actions.POST.model_type.choices',
    transform: (item: any) => {
      return {
        value: item.value,
        label: item.display_name
      };
    }
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'enabled',
        label: t`Enabled`,
        description: t`Filter by enabled status`,
        type: 'boolean'
      },
      {
        name: 'model_type',
        label: t`Model Type`,
        description: t`Filter by target model type`,
        choices: modelTypeFilters.choices
      }
    ];
  }, [modelTypeFilters.choices]);

  return (
    <>
      {newTemplate.modal}
      {editTemplate.modal}
      {deleteTemplate.modal}
      <DetailDrawer
        title={t`Edit Template`}
        size={'90%'}
        closeOnEscape={false}
        renderContent={(id) => {
          return <TemplateDrawer id={id ?? ''} templateProps={templateProps} />;
        }}
      />
      <InvenTreeTable
        url={apiUrl(templateEndpoint)}
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
