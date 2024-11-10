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
import {
  hideNotification,
  notifications,
  showNotification
} from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconDeviceFloppy,
  IconExclamationCircle,
  IconRefresh
} from '@tabler/icons-react';
import Split from '@uiw/react-split';
import type React from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { api } from '../../../App';
import { ModelType } from '../../../enums/ModelType';
import type { TablerIconType } from '../../../functions/icons';
import { apiUrl } from '../../../states/ApiState';
import type { TemplateI } from '../../../tables/settings/TemplateTable';
import { Boundary } from '../../Boundary';
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
  icon?: TablerIconType;
  component: EditorComponent;
};

type PreviewAreaProps = {};

export type PreviewAreaRef = {
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
  icon: TablerIconType;
  component: PreviewAreaComponent;
};

export type TemplateEditorProps = {
  templateUrl: string;
  printingUrl: string;
  editors: Editor[];
  previewAreas: PreviewArea[];
  template: TemplateI;
};

export function TemplateEditor(props: Readonly<TemplateEditorProps>) {
  const { templateUrl, editors, previewAreas, template } = props;
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
    if (!templateUrl) return;

    api.get(templateUrl).then((response: any) => {
      if (response.data?.template) {
        api
          .get(response.data.template)
          .then((res) => {
            codeRef.current = res.data;
            loadCodeToEditor(res.data);
          })
          .catch(() => {
            console.error(
              `ERR: Could not load template from ${response.data.template}`
            );
            codeRef.current = undefined;
            hideNotification('template-load-error');
            showNotification({
              id: 'template-load-error',
              title: t`Error`,
              message: t`Could not load the template from the server.`,
              color: 'red'
            });
          });
      }
    });
  }, [templateUrl]);

  useEffect(() => {
    if (codeRef.current === undefined) return;
    loadCodeToEditor(codeRef.current);
  }, [editorValue]);

  const updatePreview = useCallback(
    async (confirmed: boolean, saveTemplate = true) => {
      if (!confirmed) {
        openConfirmModal({
          title: t`Save & Reload Preview`,
          children: (
            <Alert
              color='yellow'
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

          notifications.hide('template-preview');

          showNotification({
            title: t`Preview updated`,
            message: t`The preview has been updated successfully.`,
            color: 'green',
            id: 'template-preview'
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
    () =>
      ModelInformationDict[template.model_type ?? ModelType.stockitem]
        .api_endpoint,
    [template]
  );

  const templateFilters: Record<string, string> = useMemo(() => {
    // TODO: Extract custom filters from template (make this more generic)
    if (template.model_type === ModelType.stockitem) {
      return { part_detail: 'true' } as Record<string, string>;
    }

    return {};
  }, [template]);

  useEffect(() => {
    api
      .get(apiUrl(previewApiUrl), { params: { limit: 1, ...templateFilters } })
      .then((res) => {
        if (res.data.results.length === 0) return;
        setPreviewItem(res.data.results[0].pk);
      });
  }, [previewApiUrl, templateFilters]);

  return (
    <Boundary label='TemplateEditor'>
      <Stack style={{ height: '100%', flex: '1' }}>
        <Split style={{ gap: '10px' }}>
          <Tabs
            value={editorValue}
            onChange={async (v) => {
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
              {editors.map((Editor, index) => {
                return (
                  <Tabs.Tab
                    key={Editor.key}
                    value={Editor.key}
                    leftSection={Editor.icon && <Editor.icon size='0.8rem' />}
                  >
                    {Editor.name}
                  </Tabs.Tab>
                );
              })}

              <Group justify='right' style={{ flex: '1' }} wrap='nowrap'>
                <SplitButton
                  loading={isPreviewLoading}
                  defaultSelected='preview_save'
                  name='preview-options'
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
                      name: t`Save & Reload Preview`,
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
            onChange={setPreviewValue}
            keepMounted={false}
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
                  leftSection={
                    PreviewArea.icon && <PreviewArea.icon size='0.8rem' />
                  }
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
                  label: t`Select instance to preview`,
                  model: template.model_type,
                  value: previewItem,
                  filters: templateFilters,
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
                    <Overlay color='red' center blur={0.2}>
                      <CloseButton
                        onClick={() => setErrorOverlay(null)}
                        style={{
                          position: 'absolute',
                          top: '10px',
                          right: '10px',
                          color: '#fff'
                        }}
                        variant='filled'
                      />
                      <Alert
                        color='red'
                        icon={<IconExclamationCircle />}
                        title={t`Error rendering template`}
                        mx='10px'
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
    </Boundary>
  );
}
