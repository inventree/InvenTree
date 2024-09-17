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
import { EditorComponent } from '../editors/TemplateEditor/TemplateEditor';

// Definition of the plugin ui feature properties, provided by the server API
export type PluginUIFeatureProps = (
  | {
      feature_type: 'template_editor';
      options: {
        title: string;
        slug: string;
      };
    }
  | {
      feature_type: 'template_preview';
      options: {
        title: string;
        slug: string;
      };
    }
) & {
  source: string;
};

export type TemplateEditorRenderContextType = {
  registerHandlers: (params: {
    setCode: (code: string) => void;
    getCode: () => string;
  }) => void;
  template: TemplateI;
};

export const getPluginTemplateEditor = (func: any, template: any) =>
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
          await func(elRef.current, {
            registerHandlers: ({ getCode, setCode }) => {
              setCodeRef.current = setCode;
              getCodeRef.current = getCode;

              if (initialCodeRef.current) {
                setCode(initialCodeRef.current);
              }
            },
            template
          } as TemplateEditorRenderContextType);
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
            title={t`Error Loading Plugin`}
            icon={<IconExclamationCircle />}
          >
            <Text>{error}</Text>
          </Alert>
        )}
        <div ref={elRef as any} style={{ display: 'flex', flex: 1 }}></div>
      </Stack>
    );
  }) as EditorComponent;
