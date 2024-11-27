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

import type { TemplateI } from '../../tables/settings/TemplateTable';
import type {
  EditorComponent,
  PreviewAreaComponent,
  PreviewAreaRef
} from '../editors/TemplateEditor/TemplateEditor';
import type {
  PluginUIFuncWithoutInvenTreeContextType,
  TemplateEditorUIFeature,
  TemplatePreviewUIFeature
} from './PluginUIFeatureTypes';

/**
 * Enumeration for available plugin UI feature types.
 */
export enum PluginUIFeatureType {
  dashboard = 'dashboard',
  panel = 'panel',
  template_editor = 'template_editor',
  template_preview = 'template_preview'
}

/**
 * Type definition for a UI component which can be loaded via plugin.
 * Ref: src/backend/InvenTree/plugin/base/ui/serializers.py:PluginUIFeatureSerializer
 *
 * @param plugin_name: The name of the plugin
 * @param feature_type: The type of the UI feature (see PluginUIFeatureType)
 * @param key: The unique key for the feature (used to identify the feature in the DOM)
 * @param title: The title of the feature (human readable)
 * @param description: A description of the feature (human readable, optional)
 * @param options: Additional options for the feature (optional, depends on the feature type)
 * @param context: Additional context data passed to the rendering function (optional)
 * @param source: The source of the feature (must point to an accessible javascript module)
 *
 */
export interface PluginUIFeature {
  plugin_name: string;
  feature_type: PluginUIFeatureType;
  key: string;
  title: string;
  description?: string;
  icon?: string;
  options?: any;
  context?: any;
  source: string;
}

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
          func({
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
      <Stack gap='xs' style={{ display: 'flex', flex: 1 }}>
        {error && (
          <Alert
            color='red'
            title={t`Error Loading Plugin Editor`}
            icon={<IconExclamationCircle />}
          >
            <Text>{error}</Text>
          </Alert>
        )}
        <div ref={elRef as any} style={{ display: 'flex', flex: 1 }} />
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
          func({
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
      <Stack gap='xs' style={{ display: 'flex', flex: 1 }}>
        {error && (
          <Alert
            color='red'
            title={t`Error Loading Plugin Preview`}
            icon={<IconExclamationCircle />}
          >
            <Text>{error}</Text>
          </Alert>
        )}
        <div ref={elRef as any} style={{ display: 'flex', flex: 1 }} />
      </Stack>
    );
  }) as PreviewAreaComponent;
