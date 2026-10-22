import { ModelFeature } from '@lib/enums/ModelFeature';
import type { ModelType } from '@lib/enums/ModelType';
import type { ModelFeaturePanelFactory } from '@lib/types/Panel';
import AttachmentPanel from './AttachmentPanel';
import NotesPanel from './NotesPanel';
import ParametersPanel from './ParametersPanel';

/**
 * Lookup of panels for generic model features (as reported by the server).
 *
 * The order of entries defines the order in which the panels are displayed.
 */
export const ModelFeaturePanelLookup: Record<string, ModelFeaturePanelFactory> =
  {
    [ModelFeature.parameters]: ({ model, id, instanceInfo }) =>
      ParametersPanel({
        model_type: model as ModelType,
        model_id: id,
        parameter_count: instanceInfo.parameter_count
      }),
    [ModelFeature.attachments]: ({ model, id, instanceInfo }) =>
      AttachmentPanel({
        model_type: model as ModelType,
        model_id: id,
        attachment_count: instanceInfo.attachment_count
      }),
    [ModelFeature.notes]: ({ model, id, instanceInfo }) =>
      NotesPanel({
        model_type: model as ModelType,
        model_id: id,
        note_count: instanceInfo.note_count
      })
  };
