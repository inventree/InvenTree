import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocalState } from '../states/LocalState';

type LegacyRemoteRenderFn = (
  container: HTMLDivElement,
  ctx: InvenTreePluginContext
) => void;

type RemoteComponent = (ctx: InvenTreePluginContext) => React.ReactElement;

interface UseRemotePluginProps {
  context: InvenTreePluginContext;
  source: string;
  defaultFunctionName: string;
  containerRef: React.RefObject<HTMLDivElement | null>;
}

interface UsePluginSourceProps {
  source: string;
  defaultFunctionName?: string;
}

type RemoteModule = {
  url: string;
  mod: Record<string, unknown>;
};

function usePluginSource({
  source,
  defaultFunctionName
}: UsePluginSourceProps) {
  const { getHost } = useLocalState.getState();

  const { moduleUrl, exportName } = useMemo(() => {
    const url = new URL(source, getHost());
    const parts = url.pathname.split(':');

    return {
      exportName: parts[1] || defaultFunctionName || 'default',
      moduleUrl: url.origin + parts[0]
    };
  }, [source, defaultFunctionName, getHost]);

  return { moduleUrl, exportName };
}

export function useRemotePlugin({
  context,
  source,
  defaultFunctionName,
  containerRef
}: UseRemotePluginProps): RemoteComponent | null {
  const { moduleUrl, exportName } = usePluginSource({
    source,
    defaultFunctionName
  });
  const [remoteModule, setRemoteModule] = useState<RemoteModule | null>(null);

  const hmrSetModule = useCallback((newRemoteModule: RemoteModule) => {
    setRemoteModule((prevRemoteModule) => {
      const prevUrl = new URL(prevRemoteModule?.url ?? '');
      const newUrl = new URL(newRemoteModule.url);
      if (prevUrl.pathname === newUrl.pathname) {
        return newRemoteModule;
      }
      return prevRemoteModule;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const _mod = await import(/* @vite-ignore */ moduleUrl);

      if (!cancelled) {
        setRemoteModule({ mod: _mod, url: moduleUrl });
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [moduleUrl]);

  const legacyRenderFn = useMemo(() => {
    if (!remoteModule) return null;

    const mod = remoteModule.mod;

    const func = mod[exportName];

    if (typeof func === 'function' && func.length === 2) {
      return func as LegacyRemoteRenderFn;
    }

    return null;
  }, [remoteModule, exportName]);

  const componentFn = useMemo(() => {
    if (!remoteModule) return null;

    const mod = remoteModule.mod;

    const func = mod[exportName];

    if (typeof func === 'function' && func.length === 1) {
      return func as RemoteComponent;
    }

    return null;
  }, [remoteModule, exportName]);

  useEffect(() => {
    if (legacyRenderFn && containerRef.current) {
      legacyRenderFn(containerRef.current, context);
      (window as any).__plugin_hmr_reload = hmrSetModule;
    }

    return () => {
      delete (window as any).__plugin_hmr_reload;
    };
  }, [legacyRenderFn, context, hmrSetModule]);

  return componentFn;
}
