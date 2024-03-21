import { t } from '@lingui/macro';
import {
  Alert,
  CloseButton,
  Code,
  Group,
  Overlay,
  Stack,
  Tabs
} from '@mantine/core';
import { openConfirmModal } from '@mantine/modals';
import { showNotification } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconDeviceFloppy,
  IconExclamationCircle,
  IconRefresh,
  TablerIconsProps
} from '@tabler/icons-react';
import Split from '@uiw/react-split';
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';

import { api } from '../../../App';
import { ModelType } from '../../../enums/ModelType';
import { apiUrl } from '../../../states/ApiState';
import { TemplateI } from '../../../tables/settings/TemplateTable';
import { SplitButton } from '../../buttons/SplitButton';
import { StandaloneField } from '../../forms/StandaloneField';
import { ModelInformationDict } from '../../render/ModelType';

type EditorProps = {
  template: TemplateI;
};
type EditorRef = {
  setCode: (code: string) => void | Promise<void>;
  getCode: () => (string | undefined) | Promise<string | undefined>;
};
export type EditorComponent = React.ForwardRefExoticComponent<
  EditorProps & React.RefAttributes<EditorRef>
>;
export type Editor = {
  key: string;
  name: string;
  icon: (props: TablerIconsProps) => React.JSX.Element;
  component: EditorComponent;
};

type PreviewAreaProps = {};
type PreviewAreaRef = {
  updatePreview: (
    code: string,
    previewItem: string,
    saveTemplate: boolean,
    templateEditorProps: TemplateEditorProps
  ) => void | Promise<void>;
};
export type PreviewAreaComponent = React.ForwardRefExoticComponent<
  PreviewAreaProps & React.RefAttributes<PreviewAreaRef>
>;
export type PreviewArea = {
  key: string;
  name: string;
  icon: (props: TablerIconsProps) => React.JSX.Element;
  component: PreviewAreaComponent;
};

export type TemplatePreviewProps = {
  itemKey: string;
  model: ModelType;
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
  template: TemplateI;
};

export function TemplateEditor(props: TemplateEditorProps) {
  const { downloadUrl, editors, previewAreas, preview } = props;
  const editorRef = useRef<EditorRef>();
  const previewRef = useRef<PreviewAreaRef>();

  const [hasSaveConfirmed, setHasSaveConfirmed] = useState(false);

  const [previewItem, setPreviewItem] = useState<string>('');
  const [errorOverlay, setErrorOverlay] = useState(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const [editorValue, setEditorValue] = useState<null | string>(editors[0].key);
  const [previewValue, setPreviewValue] = useState<null | string>(
    previewAreas[0].key
  );

  const codeRef = useRef<string | undefined>();

  const loadCodeToEditor = useCallback(async (code: string) => {
    try {
      return await Promise.resolve(editorRef.current?.setCode(code));
    } catch (e: any) {
      showNotification({
        title: t`Error loading template`,
        message: e?.message ?? e,
        color: 'red'
      });
    }
  }, []);

  const getCodeFromEditor = useCallback(async () => {
    try {
      return await Promise.resolve(editorRef.current?.getCode());
    } catch (e: any) {
      showNotification({
        title: t`Error saving template`,
        message: e?.message ?? e,
        color: 'red'
      });
      return undefined;
    }
  }, []);

  useEffect(() => {
    if (!downloadUrl) return;

    api.get(downloadUrl).then((res) => {
      codeRef.current = res.data;
      loadCodeToEditor(res.data);
    });
  }, [downloadUrl]);

  useEffect(() => {
    if (codeRef.current === undefined) return;
    loadCodeToEditor(codeRef.current);
  }, [editorValue]);

  const updatePreview = useCallback(
    async (confirmed: boolean, saveTemplate: boolean = true) => {
      if (!confirmed) {
        openConfirmModal({
          title: t`Save & Reload preview?`,
          children: (
            <Alert
              color="yellow"
              icon={<IconAlertTriangle />}
              title={t`Are you sure you want to Save & Reload the preview?`}
            >
              {t`To render the preview the current template needs to be replaced on the server with your modifications which may break the label if it is under active use. Do you want to proceed?`}
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

      const code = await getCodeFromEditor();
      if (code === undefined || !previewItem) return;

      setIsPreviewLoading(true);
      Promise.resolve(
        previewRef.current?.updatePreview(
          code,
          previewItem,
          saveTemplate,
          props
        )
      )
        .then(() => {
          setErrorOverlay(null);
          showNotification({
            title: t`Preview updated`,
            message: t`The preview has been updated successfully.`,
            color: 'green'
          });
        })
        .catch((error) => {
          setErrorOverlay(error.message);
        })
        .finally(() => {
          setIsPreviewLoading(false);
        });
    },
    [previewItem]
  );

  const previewApiUrl = useMemo(
    () => ModelInformationDict[preview.model].api_endpoint,
    [preview.model]
  );

  useEffect(() => {
    api
      .get(apiUrl(previewApiUrl), { params: { limit: 1, ...preview.filters } })
      .then((res) => {
        if (res.data.results.length === 0) return;
        setPreviewItem(res.data.results[0].pk);
      });
  }, [previewApiUrl, preview.filters]);

  return (
    <Stack style={{ height: '100%', flex: '1' }}>
      <Split style={{ gap: '10px' }}>
        <Tabs
          value={editorValue}
          onTabChange={async (v) => {
            codeRef.current = await getCodeFromEditor();
            setEditorValue(v);
          }}
          keepMounted={false}
          style={{
            minWidth: '300px',
            flex: '1',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Tabs.List>
            {editors.map((Editor) => (
              <Tabs.Tab
                key={Editor.key}
                value={Editor.key}
                icon={<Editor.icon size="0.8rem" />}
              >
                {Editor.name}
              </Tabs.Tab>
            ))}

            <Group position="right" style={{ flex: '1' }} noWrap>
              <SplitButton
                loading={isPreviewLoading}
                defaultSelected="preview_save"
                options={[
                  {
                    key: 'preview',
                    name: t`Reload preview`,
                    tooltip: t`Use the currently stored template from the server`,
                    icon: IconRefresh,
                    onClick: () => updatePreview(true, false),
                    disabled: !previewItem || isPreviewLoading
                  },
                  {
                    key: 'preview_save',
                    name: t`Save & Reload preview`,
                    tooltip: t`Save the current template and reload the preview`,
                    icon: IconDeviceFloppy,
                    onClick: () => updatePreview(hasSaveConfirmed),
                    disabled: !previewItem || isPreviewLoading
                  }
                ]}
              />
            </Group>
          </Tabs.List>

          {editors.map((Editor) => (
            <Tabs.Panel
              key={Editor.key}
              value={Editor.key}
              style={{
                display: 'flex',
                flex: editorValue === Editor.key ? 1 : 0
              }}
            >
              {/* @ts-ignore-next-line */}
              <Editor.component ref={editorRef} template={props.template} />
            </Tabs.Panel>
          ))}
        </Tabs>

        <Tabs
          value={previewValue}
          onTabChange={setPreviewValue}
          style={{
            minWidth: '200px',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Tabs.List>
            {previewAreas.map((PreviewArea) => (
              <Tabs.Tab
                key={PreviewArea.key}
                value={PreviewArea.key}
                icon={<PreviewArea.icon size="0.8rem" />}
              >
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
                api_url: apiUrl(previewApiUrl),
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
            <Tabs.Panel
              key={PreviewArea.key}
              value={PreviewArea.key}
              style={{
                display: 'flex',
                flex: previewValue === PreviewArea.key ? 1 : 0
              }}
            >
              <div
                style={{
                  height: '100%',
                  position: 'relative',
                  display: 'flex',
                  flex: '1'
                }}
              >
                {/* @ts-ignore-next-line */}
                <PreviewArea.component ref={previewRef} />

                {errorOverlay && (
                  <Overlay color="red" center blur={0.2}>
                    <CloseButton
                      onClick={() => setErrorOverlay(null)}
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        color: '#fff'
                      }}
                      variant="filled"
                    />
                    <Alert
                      color="red"
                      icon={<IconExclamationCircle />}
                      title={t`Error rendering template`}
                      mx="10px"
                    >
                      <Code>{errorOverlay}</Code>
                    </Alert>
                  </Overlay>
                )}
              </div>
            </Tabs.Panel>
          ))}
        </Tabs>
      </Split>
    </Stack>
  );
}
