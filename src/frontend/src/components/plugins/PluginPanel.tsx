import { t } from '@lingui/macro';
import { Alert, Loader, LoadingOverlay, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ModelType } from '../../enums/ModelType';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import { PanelType } from '../nav/Panel';
import { PluginElementProps } from './PluginElement';

interface PluginPanelProps extends PanelType {
  source?: string;
  renderFunction?: string;
  hiddenFunction?: string;
  params?: any;
  instance?: any;
  model?: ModelType | string;
  id?: number | null;
  pluginKey: string;
}

// Placeholder content for a panel with no content
function PanelNoContent() {
  return (
    <Alert color="red" title={t`No Content`}>
      <Text>{t`No content provided for this plugin`}</Text>
    </Alert>
  );
}

// Placeholder content for a panel which has failed to load
function PanelErrorContent({ error }: { error: ReactNode | undefined }) {
  return (
    <Alert
      color="red"
      title={t`Error Loading Plugin`}
      icon={<IconExclamationCircle />}
    >
      <Text>{error}</Text>
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
export default function PluginPanel(props: PluginPanelProps): PanelType {
  return {
    ...props,
    content: `Hello world, from ${props.pluginKey}: ${props.name}`
  };

  // TODO: Get this working!
  // Note: Having these hooks below the "return" above causes errors,
  // Warning: React has detected a change in the order of Hooks called by BasePanelGroup. This will lead to bugs and errors if not fixed

  /*
  const ref = useRef<HTMLDivElement>();
  const user = useUserState();
  const navigate = useNavigate();

  const [ isLoading, setIsLoading ] = useState<boolean>(false);
  const [errorDetail, setErrorDetail] = useState<ReactNode | undefined>(
    undefined
  );

  // External module which defines the plugin content
  const [ pluginModule, setPluginModule ] = useState<any>(null);

    const host = useLocalState.getState().host;

    // Attributes to pass through to the plugin module
    const attributes : PluginElementProps= useMemo(() => {
      return {
        target: ref.current,
        model: props.model,
        id: props.id,
        instance: props.instance,
        api: api,
        user: user,
        host: host,
        navigate: navigate
      };
    }, [props, ref.current, api, user, navigate]);



  // Reload external source if the source URL changes
  useEffect(() => {
    loadExternalSource(props.source || '');
  }, [props.source]);

  // Memoize the panel rendering function
  const renderPanel = useMemo(() => {
    const renderFunction = props.renderFunction || 'renderPanel';

    console.log("renderPanel memo:", renderFunction, pluginModule);

    if (pluginModule && pluginModule[renderFunction]) {
      return pluginModule[renderFunction];
    }
    return null;
  }, [pluginModule, props.renderFunction]);

  // Memoize if the panel is hidden
  const isPanelHidden : boolean = useMemo(() => {
    const hiddenFunction = props.hiddenFunction || 'isPanelHidden';

    console.log("hiddenFunction memo:", hiddenFunction, pluginModule);
    console.log("- attributes:", attributes);

    if (pluginModule && pluginModule[hiddenFunction]) {
      return !!pluginModule[hiddenFunction](attributes);
    } else {
      return false;
    }
  }, [attributes, pluginModule, props.hiddenFunction]);

  // Construct the panel content
  const panelContent = useMemo(() => {
    if (isLoading) {
      return <Loader />;
    } else if (errorDetail) {
      return <PanelErrorContent error={errorDetail} />;
    } else if (!props.content && !props.source) {
      return <PanelNoContent />;
    } else {
      return <div ref={ref as any}></div>;
    }
  }, [props, errorDetail, isLoading]);

  // Regenerate the panel content as required
  useEffect(() => {
    // If a panel rendering function is provided, use that

    console.log("Regenerating panel content...");

    if (renderPanel) {
      console.log("- using external rendering function");
      renderPanel(attributes);
    } else if (props.content) {
      // If content is provided directly, render it into the panel
      console.log("- using direct content");
      if (ref) {
        ref.current?.setHTMLUnsafe(props.content.toString());
      }
    }
  }, [ref, renderPanel, props.content, attributes]);

  // Load external source content
  const loadExternalSource = async (source: string) => {

    const host = useLocalState.getState().host;

    if (!source) {
      setErrorDetail(undefined);
      setPluginModule(null);
      return;
    }

    if (source.startsWith('/')) {
      // Prefix the source with the host URL
      source = `${host}${source}`;
    }

    // TODO: Gate where this content may be loaded from (e.g. only allow certain domains)
    // TODO: Add a timeout for loading external content
    // TODO: Restrict to certain file types (e.g. .js)

    let errorMessage : ReactNode = undefined;

    console.log("Loading plugin module from:", source);

    setIsLoading(true);

    // Load content from external source
    const module = await import(/* @vite-ignore * / source ?? '')
      .catch((error) => {
        errorMessage = error.toString();
        return null;
      })
      .then((module) => {
        return module;
      });

    setIsLoading(false);

    console.log("Loaded plugin module:", module);

    setPluginModule(module);
    setErrorDetail(errorMessage);
  }

  // Return the panel state
  return {
    ...props,
    content: panelContent,
    hidden: isPanelHidden,
  }
  */
}
