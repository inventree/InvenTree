import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { useEffect, useState, useCallback, useMemo } from "react";
import { useLocalState } from '../states/LocalState';

type LegacyRemoteRenderFnType = (container: HTMLDivElement, ctx: InvenTreePluginContext) => void;
type RemoteComponentType = (ctx: InvenTreePluginContext) => React.ReactElement;

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

function usePluginSource({source, defaultFunctionName}: UsePluginSourceProps) {
  const { getHost } = useLocalState.getState();

  const { moduleUrl, exportName } = useMemo(() => {
    const url = new URL(source, getHost());
    const parts = url.pathname.split(":");

    return {
      exportName: parts[1] || defaultFunctionName || 'default',
      moduleUrl: url.origin + parts[0],
    };

  }, [source, defaultFunctionName, getHost]);

  return { moduleUrl, exportName };
}

export function useRemotePlugin(
    {context, source, defaultFunctionName, containerRef}: UseRemotePluginProps
): RemoteComponentType | null {
  const { moduleUrl, exportName } = usePluginSource({source, defaultFunctionName});
  const [mod, setModule] = useState<Record<string, unknown> | null>(null);

  const hmrSetModule = useCallback((mod: Record<string, unknown>) => {
    setModule(mod);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const _mod = await import(/* @vite-ignore */moduleUrl);

      if (!cancelled) {
        setModule(_mod);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [moduleUrl]);

  const legacyRenderFn = useMemo(() => {
    if (!mod) return null;

    const func = mod[exportName];

    if (typeof func === 'function' && func.length === 2) {
      return (func as LegacyRemoteRenderFnType);
    }

    return null;
  }, [mod, exportName]);

  const componentFn = useMemo(() => {
    if (!mod) return null;

    const func = mod[exportName];

    if (typeof func === 'function' && func.length === 1) {
      return (func as RemoteComponentType);
    }

    return null;
  }, [mod, exportName]);

  useEffect(() => {
    if (legacyRenderFn && containerRef.current) {
      legacyRenderFn(containerRef.current, context);
      (window as any).__plugin_hmr_reload = hmrSetModule;
    }

    return () => {
      delete (window as any).__plugin_hmr_reload;
    }
  }, [legacyRenderFn, context, hmrSetModule]);

  return componentFn;
}
