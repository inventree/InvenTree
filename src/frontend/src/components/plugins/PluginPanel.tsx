import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';
import { AxiosInstance } from 'axios';
import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ModelType } from '../../enums/ModelType';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import { PanelType } from '../nav/Panel';

interface PluginPanelProps extends PanelType {
  source?: string;
  params?: any;
  targetInstance?: any;
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
  targetId?: number | null;
  targetInstance?: any;
  api: AxiosInstance;
  user: any;
  host: string;
  navigate: any;
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
 * - model instance (already fetched via API)
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

  const host = useLocalState((s) => s.host);
  const user = useUserState();
  const navigate = useNavigate();

  const loadExternalSource = async () => {
    let source: string = props.source ?? '';

    if (!source) {
      return;
    }

    if (source.startsWith('/')) {
      // Prefix the source with the host URL
      source = `${host}${source}`;
    }

    // TODO: Gate where this content may be loaded from (e.g. only allow certain domains)

    // Load content from external source
    const module = await import(/* @vite-ignore */ source ?? '');

    // We expect the external source to define a function which will render the content
    if (
      module &&
      module.render_panel &&
      typeof module.render_panel === 'function'
    ) {
      module.render_panel({
        target: ref.current,
        props: props,
        api: api,
        host: host,
        user: user,
        navigate: navigate,
        targetModel: props.targetModel,
        targetId: props.targetId,
        targetInstance: props.targetInstance
      });
    }
  };

  useEffect(() => {
    if (props.source) {
      // Load content from external source
      loadExternalSource();
    } else if (props.content) {
      // If content is provided directly, render it into the panel
      if (ref) {
        ref.current?.setHTMLUnsafe(props.content.toString());
      }
    }
  }, [props]);

  if (!props.content && !props.source) {
    return <PanelNoContent />;
  }

  return <div ref={ref as any}></div>;
}
