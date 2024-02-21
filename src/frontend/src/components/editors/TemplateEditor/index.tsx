import { Trans, t } from '@lingui/macro';
import { Button, Code, Container, Group, Stack, Tabs } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { langs } from '@uiw/codemirror-extensions-langs';
import { vscodeDark } from '@uiw/codemirror-theme-vscode';
import CodeMirror, { EditorState, useCodeMirror } from '@uiw/react-codemirror';
import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

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
type CodeEditorComponent = React.ForwardRefExoticComponent<
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
type PreviewAreaComponent = React.ForwardRefExoticComponent<
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
    if (!code) return;

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
              <Button onClick={updatePreview}>
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

const extensions = [langs.html()];

export const CodeEditor: CodeEditorComponent = forwardRef((props, ref) => {
  const editor = useRef<HTMLDivElement | null>(null);
  const [code, setCode] = useState('');
  const { setContainer } = useCodeMirror({
    container: editor.current,
    extensions,
    value: code,
    onChange: (value) => setCode(value),
    height: '70vh',
    theme: vscodeDark
  });

  useImperativeHandle(ref, () => ({
    setCode: (code) => setCode(code),
    getCode: () => code
  }));

  useEffect(() => {
    if (editor.current) {
      setContainer(editor.current);
    }
  }, [editor.current]);

  return <div ref={editor}></div>;
});

export const PreviewArea: PreviewAreaComponent = forwardRef((props, ref) => {
  const [pdfUrl, setPdfUrl] = useState('');

  useImperativeHandle(ref, () => ({
    updatePreview: async (
      code,
      previewItem,
      { uploadKey, uploadUrl, preview: { itemKey }, templateType }
    ) => {
      const formData = new FormData();
      formData.append(uploadKey, new File([code], 'template.html'));

      const res = await api.patch(uploadUrl, formData);
      if (res.status !== 200) {
        return console.log('An error occurred while uploading the template');
      }

      let preview = await api.get(
        uploadUrl + `print/?plugin=inventreelabel&${itemKey}=${previewItem}`
      );

      if (preview.status !== 200) {
        return console.log(
          'An error occurred while fetching the preview',
          preview.data
        );
      }

      if (templateType === 'label') {
        preview = await api.get(preview.data.file, {
          responseType: 'blob'
        });
      }

      let pdf = new Blob([preview.data], {
        type: preview.headers['content-type']
      });
      let srcUrl = URL.createObjectURL(pdf);

      setPdfUrl(srcUrl + '#toolbar=0&zoom=500');
    }
  }));

  if (!pdfUrl) return <div>Preview not available.</div>;

  return (
    <div style={{ height: '60vh' }}>
      <iframe src={pdfUrl} width="100%" height="100%" />
    </div>
  );
});
