import { Trans, t } from '@lingui/macro';
import { Button, Group, Stack, Tabs } from '@mantine/core';
import React, { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '../../../App';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { ModelType } from '../../../enums/ModelType';
import { apiUrl } from '../../../states/ApiState';
import { StandaloneField } from '../../forms/StandaloneField';

type CodeEditorProps = (props: {
  ref: React.RefObject<CodeEditorRef>;
}) => React.ReactNode;
type CodeEditorRef = {
  setCode: (code: string) => void;
  getCode: () => string;
};
export type CodeEditorComponent = React.ForwardRefExoticComponent<
  CodeEditorProps & React.RefAttributes<CodeEditorRef>
>;
type CodeEditor = {
  key: string;
  name: string;
  component: CodeEditorComponent;
};

type PreviewAreaProps = (props: {
  ref: React.RefObject<CodeEditorRef>;
}) => React.ReactNode;
type PreviewAreaRef = {
  updatePreview: (
    code: string,
    previewItem: string,
    templateEditorProps: TemplateEditorProps
  ) => void;
};
export type PreviewAreaComponent = React.ForwardRefExoticComponent<
  PreviewAreaProps & React.RefAttributes<PreviewAreaRef>
>;
type PreviewArea = {
  key: string;
  name: string;
  component: PreviewAreaComponent;
};

type TemplateEditorProps = {
  downloadUrl: string;
  uploadUrl: string;
  uploadKey: string;
  preview: { itemKey: string; model: ModelType; apiUrl: ApiEndpoints };
  templateType: 'label' | 'report';
  codeEditors: CodeEditor[];
  previewAreas: PreviewArea[];
};

export function TemplateEditor(props: TemplateEditorProps) {
  const { downloadUrl, codeEditors, previewAreas, preview } = props;
  const editorRef = useRef<CodeEditorRef>();
  const previewRef = useRef<PreviewAreaRef>();

  const [previewItem, setPreviewItem] = useState<string>('');

  useEffect(() => {
    if (!downloadUrl) return;

    api.get(downloadUrl).then((res) => editorRef.current?.setCode(res.data));
  }, [downloadUrl]);

  const updatePreview = useCallback(async () => {
    const code = editorRef.current?.getCode();
    if (!code || !previewItem) return;

    previewRef.current?.updatePreview(code, previewItem, props);
  }, [previewItem]);

  return (
    <Stack>
      <Group align="start">
        <Tabs
          style={{ width: '49%' }}
          defaultValue={codeEditors[0].key}
          keepMounted={false}
        >
          <Tabs.List>
            {codeEditors.map((CodeEditor) => (
              <Tabs.Tab key={CodeEditor.key} value={CodeEditor.key}>
                {CodeEditor.name}
              </Tabs.Tab>
            ))}
          </Tabs.List>

          {codeEditors.map((CodeEditor) => (
            <Tabs.Panel key={CodeEditor.key} value={CodeEditor.key}>
              {/* @ts-ignore-next-line */}
              <CodeEditor.component ref={editorRef} />
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

            <Group position="right" style={{ flex: 1 }}>
              <Button onClick={updatePreview} disabled={!previewItem}>
                <Trans>Reload preview</Trans>
              </Button>
            </Group>
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
