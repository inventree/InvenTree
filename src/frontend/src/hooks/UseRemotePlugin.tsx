import type { InvenTreePluginContext } from '@lib/types/Plugins';
import { t } from '@lingui/core/macro';
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { useLocalState } from '../states/LocalState';

type LegacyPluginEntryFn = (
  container: HTMLDivElement,
  ctx: InvenTreePluginContext
) => void;

type PluginEntryFn = (ctx: InvenTreePluginContext) => ReactElement;

type UseRemotePluginOptions = {
  context: InvenTreePluginContext;
  source: string;
  defaultFunctionName: string;
  containerRef: React.RefObject<HTMLDivElement | null>;
};

type UsePluginSourceOptions = {
  source: string;
  defaultFunctionName?: string;
};

type UseRemotePluginReturn = {
  componentFn: PluginEntryFn | null;
  errorMsg: string | null;
  exportName: string;
  pluginContext: InvenTreePluginContext;
  remountKey: number;
};

function usePluginSource({
  source,
  defaultFunctionName
}: UsePluginSourceOptions) {
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

function getHmrCallbacks(url: string) {
  const w = window as any;
  w.__plugin_hmr_callbacks ??= {};
  w.__plugin_hmr_callbacks[url] ??= new Set<Function>();
  return w.__plugin_hmr_callbacks[url];
}

const hasHmr = import.meta.hot !== undefined;

export function useRemotePlugin({
  context,
  source,
  defaultFunctionName,
  containerRef
}: UseRemotePluginOptions): UseRemotePluginReturn {
  const { moduleUrl, exportName } = usePluginSource({
    source,
    defaultFunctionName
  });

  const [remoteModule, setRemoteModule] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [reloadVersion, setReloadVersion] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const reloadContent = useCallback(() => setReloadVersion((v) => v + 1), []);

  const hmrSetModule = useCallback(
    (newRemoteModule: Record<string, unknown> | null) => {
      if (!hasHmr) return;
      setRemoteModule(newRemoteModule);
    },
    []
  );

  useEffect(() => {
    let cancelled = false;

    setErrorMsg(null);

    const loadModule = async () => {
      try {
        const mod = await import(/* @vite-ignore */ moduleUrl);
        if (!cancelled) setRemoteModule(mod);
      } catch (err) {
        if (!cancelled) {
          console.error(`ERR: Failed to load module: ${moduleUrl}:\n${err}`);
          setErrorMsg(t`Failed to load module: ${moduleUrl}`);
        }
      }
    };

    loadModule();

    return () => {
      cancelled = true;
    };
  }, [moduleUrl]);

  const [legacyRenderFn, componentFn, error] = useMemo(() => {
    if (!remoteModule) return [null, null, null];

    let err: string | null = null;
    const func = remoteModule[exportName];

    if (typeof func === 'function') {
      if (func.length === 2) {
        return [func as LegacyPluginEntryFn, null, null];
      } else if (func.length === 1) {
        return [null, func as PluginEntryFn, null];
      } else {
        err = `Entrypoint ${exportName} in ${moduleUrl} must accept 1-2 arguments`;
      }
    } else if (func !== undefined) {
      err = t`Export ${exportName} in ${moduleUrl} is not a function (found type ${typeof func}).`;
    } else {
      err = t`Plugin entrypoint ${exportName} does not exist in ${moduleUrl}.`;
    }

    return [null, null, err];
  }, [remoteModule, exportName]);

  useEffect(() => {
    if (legacyRenderFn && containerRef.current) {
      containerRef.current.innerHTML = '';
      legacyRenderFn(containerRef.current, context);

      if (hasHmr) getHmrCallbacks(moduleUrl)?.add(hmrSetModule);
    }

    return () => {
      if (hasHmr) getHmrCallbacks(moduleUrl)?.delete(hmrSetModule);
    };
  }, [moduleUrl, legacyRenderFn, context, hmrSetModule]);

  return {
    componentFn: componentFn,
    errorMsg: error ?? errorMsg,
    exportName: exportName,
    pluginContext: { ...context, reloadContent: reloadContent },
    remountKey: reloadVersion
  };
}
