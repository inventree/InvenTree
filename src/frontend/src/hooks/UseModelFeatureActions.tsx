import { ModelFeature } from '@lib/enums/ModelFeature';
import type { ModelType } from '@lib/enums/ModelType';
import type { UserStateProps } from '@lib/types/User';
import { type ReactNode, useMemo } from 'react';
import { PrintingActions } from '../components/buttons/PrintingActions';
import {
  type ActionDropdownItem,
  BarcodeActionDropdown
} from '../components/items/ActionDropdown';
import { useModelFeatures } from '../states/ModelFeatureState';
import { useUserState } from '../states/UserState';

type FeatureOverrides<T> = Partial<Record<ModelFeature, T>>;
type ModelFeatureActionFactory = (context: {
  model: ModelType;
  pk: number;
  instance: any;
  user: UserStateProps;
  permission?: boolean;
  actions?: ActionDropdownItem[];
  enabled?: FeatureOverrides<boolean>;
}) => ReactNode | null;

const modelFeatureActionLookup: Partial<
  Record<ModelFeature, ModelFeatureActionFactory>
> = {
  [ModelFeature.barcode]: ({
    model,
    pk,
    instance,
    user,
    permission,
    actions
  }) => (
    <BarcodeActionDropdown
      key='barcode-actions'
      model={model}
      pk={pk}
      hash={instance.barcode_hash}
      perm={permission ?? user.hasChangePermission(model)}
      actions={actions}
    />
  ),
  [ModelFeature.report]: ({ model, pk, enabled }) => {
    const labels = enabled?.[ModelFeature.label] ?? true;
    const reports = enabled?.[ModelFeature.report] ?? true;

    return labels || reports ? (
      <PrintingActions
        key='printing-actions'
        modelType={model}
        items={[pk]}
        enableLabels={labels}
        enableReports={reports}
      />
    ) : null;
  }
};

/**
 * use generic modelfeature detection to render model feature actions (e.g. barcode and printing actions)
 *
 * @param model - The model type
 * @param instance - The model instance
 * @param actions - Additional actions keyed by model feature
 * @param permission - Permission overrides keyed by model feature
 * @param enabled - Disable individual model features
 */
export function useModelFeatureActions({
  model,
  instance,
  actions: extraActions,
  permission,
  enabled
}: {
  model: ModelType;
  instance: any;
  actions?: FeatureOverrides<ActionDropdownItem[]>;
  permission?: FeatureOverrides<boolean>;
  enabled?: FeatureOverrides<boolean>;
}): ReactNode[] {
  const user = useUserState();
  const features = useModelFeatures(model);

  return useMemo(() => {
    const pk: number | undefined = instance?.pk;

    if (!pk) {
      return [];
    }

    return Object.values(ModelFeature).flatMap((feature) => {
      const featureEnabled = enabled?.[feature];
      if (!features.includes(feature) || featureEnabled === false) {
        return [];
      }

      const constAction = modelFeatureActionLookup[feature];
      if (!constAction) {
        return [];
      }

      const action = constAction({
        model,
        pk,
        instance,
        user,
        permission: permission?.[feature],
        actions: extraActions?.[feature],
        enabled: enabled
      });

      return action === null ? [] : [action];
    });
  }, [model, instance, features, user, extraActions, permission, enabled]);
}
