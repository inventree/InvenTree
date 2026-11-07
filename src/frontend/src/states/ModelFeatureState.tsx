import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelFeature } from '@lib/enums/ModelFeature';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { api } from '../App';
import { useUserState } from './UserState';

export type ModelFeatureLookup = Record<ModelType | string, ModelFeatureRef[]>;
export type ModelFeatureRef = ModelFeature | (string & {});

interface ModelFeatureStateProps {
  features?: ModelFeatureLookup;
  fetchFeatures: () => Promise<void>;
  hasFeature: (model: ModelType | string, feature: ModelFeatureRef) => boolean;
}

/**
 * State for tracking which generic features each model type supports.
 * This is static per server instance, so is fetched once with the global states.
 */
export const useModelFeatureState = create<ModelFeatureStateProps>()(
  persist(
    (set, get) => ({
      features: undefined,
      fetchFeatures: async () => {
        const { isLoggedIn } = useUserState.getState();

        if (!isLoggedIn()) {
          return;
        }

        // Feature information is provided by the content type API
        await api
          .get(apiUrl(ApiEndpoints.content_type_list), {
            params: { features: true }
          })
          .then((response) => {
            const lookup: ModelFeatureLookup = {};

            for (const contentType of response.data ?? []) {
              lookup[contentType.model] = contentType.features ?? [];
            }

            set({ features: lookup });
          })
          .catch(() => {
            console.error('ERR: Error fetching model feature information');
          });
      },
      hasFeature: (model: ModelType | string, feature: ModelFeatureRef) => {
        return get().features?.[model]?.includes(feature) ?? false;
      }
    }),
    {
      name: 'model-feature-state',
      version: 1,
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ features: state.features })
    }
  )
);

const EMPTY_FEATURES: ModelFeatureRef[] = [];

/**
 * Hook to get list of features for given model type.
 * Returns an empty list if the model is unknown, or the information is not (yet) loaded.
 */
export function useModelFeatures(
  model: ModelType | string | undefined
): ModelFeatureRef[] {
  return useModelFeatureState(
    (state) => (model ? state.features?.[model] : undefined) ?? EMPTY_FEATURES
  );
}
