import { Trans, t } from '@lingui/macro';
import { Alert, Button, Group, Stack, Tabs } from '@mantine/core';
import { openConfirmModal } from '@mantine/modals';
import { showNotification } from '@mantine/notifications';
import React, { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '../../../App';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { apiUrl } from '../../../states/ApiState';
import { StandaloneField } from '../../forms/StandaloneField';

type EditorProps = (props: {
  ref: React.RefObject<EditorRef>;
}) => React.ReactNode;
type EditorRef = {
  setCode: (code: string) => void;
  getCode: () => string;
};
export type EditorComponent = React.ForwardRefExoticComponent<
  EditorProps & React.RefAttributes<EditorRef>
>;
type Editor = {
  key: string;
  name: string;
  component: EditorComponent;
};

type PreviewAreaProps = (props: {
  ref: React.RefObject<EditorRef>;
}) => React.ReactNode;
type PreviewAreaRef = {
  updatePreview: (
    code: string,
    previewItem: string,
    templateEditorProps: TemplateEditorProps
  ) => void | Promise<void>;
};
export type PreviewAreaComponent = React.ForwardRefExoticComponent<
  PreviewAreaProps & React.RefAttributes<PreviewAreaRef>
>;
type PreviewArea = {
  key: string;
  name: string;
  component: PreviewAreaComponent;
};

export type TemplatePreviewProps = {
  itemKey: string;
  model: ModelType;
  apiUrl: ApiEndpoints;
  filters?: Record<string, any>;
};

type TemplateEditorProps = {
  downloadUrl: string;
  uploadUrl: string;
  uploadKey: string;
  preview: TemplatePreviewProps;
  templateType: 'label' | 'report';
  editors: Editor[];
  previewAreas: PreviewArea[];
};

export function TemplateEditor(props: TemplateEditorProps) {
  const { downloadUrl, editors, previewAreas, preview } = props;
  const editorRef = useRef<EditorRef>();
  const previewRef = useRef<PreviewAreaRef>();

  const [hasSaveConfirmed, setHasSaveConfirmed] = useState(false);

  const [previewItem, setPreviewItem] = useState<string>('');

  useEffect(() => {
    if (!downloadUrl) return;

    api.get(downloadUrl).then((res) => editorRef.current?.setCode(res.data));
  }, [downloadUrl]);

  const updatePreview = useCallback(
    async (confirmed: boolean) => {
      if (!confirmed) {
        openConfirmModal({
          title: t`Save & Reload preview?`,
          children: (
            <Alert
              color="yellow"
              title={t`Are you sure you want to Save & Reload the preview?`}
            >
              {t`To render the preview the current template will be replaced with your modifications and the preview will be reloaded. Do you want to proceed?`}
            </Alert>
          ),
          labels: {
            confirm: t`Save & Reload`,
            cancel: t`Cancel`
          },
          confirmProps: {
            color: 'yellow'
          },
          onConfirm: () => {
            setHasSaveConfirmed(true);
            updatePreview(true);
          }
        });
        return;
      }

      const code = editorRef.current?.getCode();
      if (!code || !previewItem) return;

      Promise.resolve(
        previewRef.current?.updatePreview(code, previewItem, props)
      )
        .then(() => {
          showNotification({
            title: t`Preview updated`,
            message: t`The preview has been updated successfully.`,
            color: 'green'
          });
        })
        .catch((error) => {
          showNotification({
            title: t`An error occurred while updating the preview.`,
            message: error.message,
            color: 'red'
          });
        });
    },
    [previewItem]
  );

  useEffect(() => {
    api
      .get(apiUrl(preview.apiUrl), { params: { limit: 1, ...preview.filters } })
      .then((res) => {
        if (res.data.results.length === 0) return;
        setPreviewItem(res.data.results[0].pk);
      });
  }, [preview.apiUrl]);

  return (
    <Stack>
      <Group align="start">
        <Tabs
          style={{ width: '49%' }}
          defaultValue={editors[0].key}
          keepMounted={false}
        >
          <Tabs.List>
            {editors.map((Editor) => (
              <Tabs.Tab key={Editor.key} value={Editor.key}>
                {Editor.name}
              </Tabs.Tab>
            ))}

            <Group position="right" style={{ flex: 1 }}>
              <Button
                onClick={() => updatePreview(hasSaveConfirmed)}
                disabled={!previewItem}
              >
                <Trans>Save & Reload preview</Trans>
              </Button>
            </Group>
          </Tabs.List>

          {editors.map((Editor) => (
            <Tabs.Panel key={Editor.key} value={Editor.key}>
              {/* @ts-ignore-next-line */}
              <Editor.component ref={editorRef} />
            </Tabs.Panel>
          ))}
        </Tabs>

        <Tabs style={{ width: '49%' }} defaultValue={previewAreas[0].key}>
          <Tabs.List>
            {previewAreas.map((PreviewArea) => (
              <Tabs.Tab key={PreviewArea.key} value={PreviewArea.key}>
                {PreviewArea.name}
              </Tabs.Tab>
            ))}
          </Tabs.List>

          <div
            style={{
              minWidth: '100%',
              paddingBottom: '10px',
              paddingTop: '10px'
            }}
          >
            <StandaloneField
              fieldDefinition={{
                field_type: 'related field',
                api_url: apiUrl(preview.apiUrl),
                description: '',
                label: t`Select` + ' ' + preview.model + ' ' + t`to preview`,
                model: preview.model,
                value: previewItem,
                filters: preview.filters,
                onValueChange: (value) => setPreviewItem(value)
              }}
            />
          </div>

          {previewAreas.map((PreviewArea) => (
            <Tabs.Panel key={PreviewArea.key} value={PreviewArea.key}>
              {/* @ts-ignore-next-line */}
              <PreviewArea.component ref={previewRef} />
            </Tabs.Panel>
          ))}
        </Tabs>
      </Group>
    </Stack>
  );
}
