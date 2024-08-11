import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';
import { AxiosInstance } from 'axios';
import { useEffect, useRef } from 'react';

import { api } from '../../App';
import { ModelType } from '../../enums/ModelType';
import { PanelType } from '../nav/Panel';

interface PluginPanelProps extends PanelType {
  src?: string;
  params?: any;
  targetModel?: ModelType | string;
  targetId?: string | number | null;
}

/*
 * Definition of what we pass into a plugin panel
 */
interface PluginPanelParameters {
  target: HTMLDivElement;
  props: PluginPanelProps;
  targetModel?: ModelType | string;
  targetId?: number;
  api: AxiosInstance;
}

// Placeholder content for a panel with no content
function PanelNoContent() {
  return (
    <Alert color="red" title={t`No Content`}>
      <Text>{t`No content provided for this plugin`}</Text>
    </Alert>
  );
}

/**
 * TODO: Provide more context information to the plugin renderer:
 *
 * - api instance
 * - custom context data from server
 */

/**
 * A custom panel which can be used to display plugin content.
 *
 * - Content is loaded dynamically (via the API) when a page is first loaded
 * - Content can be provided from an external javascript module, or with raw HTML
 *
 * If content is provided from an external source, it is expected to define a function `render_panel` which will render the content.
 * const render_panel = (element: HTMLElement, params: any) => {...}
 *
 * Where:
 *  - `element` is the HTML element to render the content into
 *  - `params` is the set of run-time parameters to pass to the content rendering function
 */
export default function PluginPanel({ props }: { props: PluginPanelProps }) {
  const ref = useRef<HTMLDivElement>();

  const loadExternalSource = async () => {
    // Load content from external source
    const src = await import(/* @vite-ignore */ props.src ?? '');

    // We expect the external source to define a function which will render the content
    if (src && src.render_panel && typeof src.render_panel === 'function') {
      src.render_panel({
        target: ref.current,
        props: props,
        api: api,
        targetModel: props.targetModel,
        targetId: props.targetId
      });
    }
  };

  useEffect(() => {
    if (props.src) {
      // Load content from external source
      loadExternalSource();
    } else if (props.content) {
      // If content is provided directly, render it into the panel
      // ref.current.innerHTML = props.content;
    } else {
      // Something... went wrong?
    }
  }, [props]);

  if (!props.content && !props.src) {
    return <PanelNoContent />;
  }

  return <div ref={ref as any}>{props.content}</div>;
}
