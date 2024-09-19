import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState
} from 'react';

import { TemplateI } from '../../tables/settings/TemplateTable';
import {
  EditorComponent,
  PreviewAreaComponent,
  PreviewAreaRef
} from '../editors/TemplateEditor/TemplateEditor';
import {
  PluginUIFuncWithoutInvenTreeContextType,
  TemplateEditorUIFeature,
  TemplatePreviewUIFeature
} from './PluginUIFeatureTypes';

export const getPluginTemplateEditor = (
  func: PluginUIFuncWithoutInvenTreeContextType<TemplateEditorUIFeature>,
  template: TemplateI
) =>
  forwardRef((props, ref) => {
    const elRef = useRef<HTMLDivElement>();
    const [error, setError] = useState<string | undefined>(undefined);

    const initialCodeRef = useRef<string>();
    const setCodeRef = useRef<(code: string) => void>();
    const getCodeRef = useRef<() => string>();

    useImperativeHandle(ref, () => ({
      setCode: (code) => {
        // if the editor is not yet initialized, store the initial code in a ref to set it later
        if (setCodeRef.current) {
          setCodeRef.current(code);
        } else {
          initialCodeRef.current = code;
        }
      },
      getCode: () => getCodeRef.current?.()
    }));

    useEffect(() => {
      (async () => {
        try {
          await func({
            ref: elRef.current!,
            registerHandlers: ({ getCode, setCode }) => {
              setCodeRef.current = setCode;
              getCodeRef.current = getCode;

              if (initialCodeRef.current) {
                setCode(initialCodeRef.current);
              }
            },
            template
          });
        } catch (error) {
          setError(t`Error occurred while rendering the template editor.`);
          console.error(error);
        }
      })();
    }, []);

    return (
      <Stack gap="xs" style={{ display: 'flex', flex: 1 }}>
        {error && (
          <Alert
            color="red"
            title={t`Error Loading Plugin Editor`}
            icon={<IconExclamationCircle />}
          >
            <Text>{error}</Text>
          </Alert>
        )}
        <div ref={elRef as any} style={{ display: 'flex', flex: 1 }}></div>
      </Stack>
    );
  }) as EditorComponent;

export const getPluginTemplatePreview = (
  func: PluginUIFuncWithoutInvenTreeContextType<TemplatePreviewUIFeature>,
  template: TemplateI
) =>
  forwardRef((props, ref) => {
    const elRef = useRef<HTMLDivElement>();
    const [error, setError] = useState<string | undefined>(undefined);

    const updatePreviewRef = useRef<PreviewAreaRef['updatePreview']>();

    useImperativeHandle(ref, () => ({
      updatePreview: (...args) => updatePreviewRef.current?.(...args)
    }));

    useEffect(() => {
      (async () => {
        try {
          await func({
            ref: elRef.current!,
            registerHandlers: ({ updatePreview }) => {
              updatePreviewRef.current = updatePreview;
            },
            template
          });
        } catch (error) {
          setError(t`Error occurred while rendering the template preview.`);
          console.error(error);
        }
      })();
    }, []);

    return (
      <Stack gap="xs" style={{ display: 'flex', flex: 1 }}>
        {error && (
          <Alert
            color="red"
            title={t`Error Loading Plugin Preview`}
            icon={<IconExclamationCircle />}
          >
            <Text>{error}</Text>
          </Alert>
        )}
        <div ref={elRef as any} style={{ display: 'flex', flex: 1 }}></div>
      </Stack>
    );
  }) as PreviewAreaComponent;
