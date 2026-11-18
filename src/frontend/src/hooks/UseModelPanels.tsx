import type { ModelType } from '@lib/enums/ModelType';
import type { PanelType } from '@lib/types/Panel';
import { useEffect, useMemo, useState } from 'react';
import { ModelFeaturePanelLookup } from '../components/panels/ModelFeaturePanels';
import { useModelFeatures } from '../states/ModelFeatureState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsStates';
import { useInstanceInfo } from './UseInstanceInfo';

/**
 * Append panels for generic model features (e.g. parameters, attachments, notes)
 * to a set of panels, based on the features which the target model supports on the server.
 *
 * Works for any model type known to the server, including plugin defined models.
 * Panels which are already defined (by name) in the provided list are not replaced.
 */
export function useModelPanels({
  model,
  id,
  panels
}: {
  model?: ModelType | string;
  id?: number | null;
  panels: PanelType[];
}): PanelType[] {
  const features = useModelFeatures(model);
  const featureFactories = useMemo(
    () =>
      Object.entries(ModelFeaturePanelLookup)
        .filter(([feature]) => features.includes(feature))
        .map(([, factory]) => factory),
    [features]
  );
  const [loadedPanels, setLoadedPanels] = useState<{
    model: string;
    id: number;
    panels: PanelType[];
  }>();
  const { instanceInfo } = useInstanceInfo({
    modelType: featureFactories.length > 0 ? (model as ModelType) : undefined,
    modelId: id ?? undefined
  });
  const userSettings = useUserSettingsState();
  const globalSettings = useGlobalSettingsState();

  // lazy load feature panels
  useEffect(() => {
    if (!model || !id || featureFactories.length === 0) {
      return;
    }

    let cancelled = false;

    Promise.all(
      featureFactories.map((factory) =>
        factory({
          model,
          id,
          instanceInfo: { ...instanceInfo },
          userSettings,
          globalSettings
        })
      )
    )
      .then((panels) => {
        if (!cancelled) {
          setLoadedPanels({ model, id, panels });
        }
      })
      .catch((error: unknown) => {
        console.error('ERR: Error loading model feature panels', error);
      });

    return () => {
      cancelled = true;
    };
  }, [model, id, featureFactories, instanceInfo, userSettings, globalSettings]);

  return useMemo(() => {
    if (
      !model ||
      !id ||
      loadedPanels?.model !== model ||
      loadedPanels.id !== id
    ) {
      return panels;
    }

    const existing = new Set(panels.map((panel) => panel.name));
    const featurePanels = loadedPanels.panels.filter(
      (panel) => !existing.has(panel.name)
    );

    return [...panels, ...featurePanels];
  }, [model, id, panels, loadedPanels]);
}
