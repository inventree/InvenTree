import { ModelFeature } from '@lib/enums/ModelFeature';
import type { ModelType } from '@lib/enums/ModelType';
import type { ModelFeaturePanelFactory } from '@lib/types/Panel';

/**
 * Lookup of panels for generic model features (as reported by the server).
 *
 * The order of entries defines the order in which the panels are displayed.
 */
export const ModelFeaturePanelLookup: Record<string, ModelFeaturePanelFactory> =
  {
    [ModelFeature.parameters]: async ({ model, id, instanceInfo }) => {
      const { default: ParametersPanel } = await import('./ParametersPanel');
      return ParametersPanel({
        model_type: model as ModelType,
        model_id: id,
        parameter_count: instanceInfo.parameter_count
      });
    },
    [ModelFeature.attachments]: async ({ model, id, instanceInfo }) => {
      const { default: AttachmentPanel } = await import('./AttachmentPanel');
      return AttachmentPanel({
        model_type: model as ModelType,
        model_id: id,
        attachment_count: instanceInfo.attachment_count
      });
    },
    [ModelFeature.notes]: async ({ model, id, instanceInfo }) => {
      const { default: NotesPanel } = await import('./NotesPanel');
      return NotesPanel({
        model_type: model as ModelType,
        model_id: id,
        note_count: instanceInfo.note_count
      });
    },
    [ModelFeature.history]: async ({
      model,
      id,
      userSettings,
      globalSettings
    }) => {
      const { default: HistoryPanel } = await import('./HistoryPanel');
      const visible =
        globalSettings.isSet('AUDIT_LOG_ENABLED') &&
        userSettings.isSet('DISPLAY_HISTORY_TAB', false);
      return HistoryPanel({
        model_type: model as ModelType,
        model_id: id,
        visible
      });
    }
  };
