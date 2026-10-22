import type { ModelType } from '@lib/enums/ModelType';
import type { ModelFeaturePanelFactory, PanelType } from '@lib/types/Panel';
import { useMemo } from 'react';
import { ModelFeaturePanelLookup } from '../components/panels/ModelFeaturePanels';
import { useModelFeatures } from '../states/ModelFeatureState';
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
  const factories: ModelFeaturePanelFactory[] = useMemo(
    () =>
      Object.entries(ModelFeaturePanelLookup)
        .filter(([feature]) => features.includes(feature))
        .map(([, factory]) => factory),
    [features]
  );

  const { instanceInfo } = useInstanceInfo({
    modelType: factories.length > 0 ? (model as ModelType) : undefined,
    modelId: id ?? undefined
  });

  return useMemo(() => {
    if (!model || !id || factories.length == 0) {
      return panels;
    }

    const existing = new Set(panels.map((panel) => panel.name));

    const featurePanels = factories
      .map((factory) =>
        factory({
          model: model,
          id: id,
          instanceInfo: { ...instanceInfo }
        })
      )
      .filter((panel) => !existing.has(panel.name));

    return [...panels, ...featurePanels];
  }, [model, id, panels, factories, instanceInfo]);
}
