import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Button,
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
  IconDeviceFloppy,
  IconDots,
  IconExclamationCircle,
  IconRefresh
} from '@tabler/icons-react';
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
import { StandaloneField } from '../../forms/StandaloneField';
import { ActionDropdown } from '../../items/ActionDropdown';
import { ModelInformationDict } from '../../render/ModelType';

type EditorProps = (props: {
  ref: React.RefObject<EditorRef>;
  template: TemplateI;
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
    saveTemplate: boolean,
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
  const [lastUsedAction, setLastUsedAction] = useState<
    'preview' | 'preview_save'
  >('preview_save');

  const [previewItem, setPreviewItem] = useState<string>('');
  const [errorOverlay, setErrorOverlay] = useState(null);

  useEffect(() => {
    if (!downloadUrl) return;

    api.get(downloadUrl).then((res) => editorRef.current?.setCode(res.data));
  }, [downloadUrl]);

  const updatePreview = useCallback(
    async (confirmed: boolean, saveTemplate: boolean = true) => {
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
                style={{ marginRight: '-10px' }}
                onClick={() =>
                  updatePreview(
                    lastUsedAction === 'preview' ? true : hasSaveConfirmed,
                    lastUsedAction === 'preview_save'
                  )
                }
                disabled={!previewItem}
              >
                {lastUsedAction === 'preview_save' ? (
                  <Trans>Save & Reload preview</Trans>
                ) : (
                  <Trans>Reload preview</Trans>
                )}
              </Button>
              <ActionDropdown
                tooltip={t`Preview&Save Actions`}
                icon={<IconDots />}
                actions={[
                  {
                    name: t`Reload preview`,
                    tooltip: t`Use the currently stored template from the server`,
                    icon: <IconRefresh />,
                    onClick: () => {
                      setLastUsedAction('preview');
                      updatePreview(true, false);
                    },
                    disabled: !previewItem
                  },
                  {
                    name: t`Save & Reload preview`,
                    tooltip: t`Save the current template and reload the preview`,
                    icon: <IconDeviceFloppy />,
                    onClick: () => {
                      updatePreview(hasSaveConfirmed);
                      setLastUsedAction('preview_save');
                    },
                    disabled: !previewItem
                  }
                ]}
              />
            </Group>
          </Tabs.List>

          {editors.map((Editor) => (
            <Tabs.Panel key={Editor.key} value={Editor.key}>
              {/* @ts-ignore-next-line */}
              <Editor.component ref={editorRef} template={props.template} />
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
            <Tabs.Panel key={PreviewArea.key} value={PreviewArea.key}>
              <div style={{ height: '60vh', position: 'relative' }}>
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
      </Group>
    </Stack>
  );
}
