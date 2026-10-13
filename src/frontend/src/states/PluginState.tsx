import type { setRenderProps } from '@lib/states/types';
import type { InstanceRenderInterface } from '@lib/types/Rendering';
import type { ReactNode } from 'react';
import { create } from 'zustand';

interface PluginStateProps {
  customRenders: Record<
    string,
    (props: Readonly<InstanceRenderInterface>) => ReactNode
  >;
  getRenderer: (
    model: string
  ) => ((props: Readonly<InstanceRenderInterface>) => ReactNode) | undefined;
  setRenderer: setRenderProps;
}

/**
 * Global state manager for handling plugin-provided states, such as custom renderers for models.
 * This allows plugins to register custom renderers for specific models
 */
export const usePluginState = create<PluginStateProps>()((set, get) => ({
  customRenders: {},
  getRenderer: (model: string) => {
    return get().customRenders[model] || undefined;
  },
  setRenderer: (
    model: string,
    renderer: (props: Readonly<InstanceRenderInterface>) => ReactNode
  ) => {
    // ensure model is not already registered
    if (get().customRenders[model]) {
      return;
    }
    set((state) => ({
      customRenders: {
        ...state.customRenders,
        [model]: renderer
      }
    }));
  }
}));
