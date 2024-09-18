import { ModelType } from '../../enums/ModelType';
import { InvenTreeIconType } from '../../functions/icons';
import { TemplateI } from '../../tables/settings/TemplateTable';
import { TemplateEditorProps } from '../editors/TemplateEditor/TemplateEditor';
import { InvenTreeContext } from './PluginContext';

// #region  Type Helpers
export type BaseUIFeature = {
  featureType: string;
  requestContext: Record<string, any>;
  responseOptions: Record<string, any>;
  renderContext: Record<string, any>;
  renderReturnType: any;
};

export type PluginUIGetFeatureType<T extends BaseUIFeature> = (params: {
  renderContext: T['renderContext'];
  inventreeContext: InvenTreeContext;
}) => T['renderReturnType'];

export type PluginUIFuncWithoutInvenTreeContextType<T extends BaseUIFeature> = (
  renderContext: T['renderContext']
) => T['renderReturnType'];

export type PluginUIFeatureAPIResponse<T extends BaseUIFeature> = {
  feature_type: T['featureType'];
  options: T['responseOptions'];
  source: string;
};

// #region Types
export type TemplateEditorUIFeature = {
  featureType: 'template_editor';
  requestContext: {
    template_type: ModelType.labeltemplate | ModelType.reporttemplate;
    template_model: ModelType;
  };
  responseOptions: {
    key: string;
    title: string;
    icon: InvenTreeIconType;
  };
  renderContext: {
    ref: HTMLDivElement;
    registerHandlers: (handlers: {
      setCode: (code: string) => void;
      getCode: () => string;
    }) => void;
    template: TemplateI;
  };
  renderReturnType: void;
};

export type TemplatePreviewUIFeature = {
  featureType: 'template_preview';
  requestContext: {
    template_type: ModelType.labeltemplate | ModelType.reporttemplate;
    template_model: ModelType;
  };
  responseOptions: {
    key: string;
    title: string;
    icon: InvenTreeIconType;
  };
  renderContext: {
    ref: HTMLDivElement;
    template: TemplateI;
    registerHandlers: (handlers: {
      updatePreview: (
        code: string,
        previewItem: string,
        saveTemplate: boolean,
        templateEditorProps: TemplateEditorProps
      ) => void | Promise<void>;
    }) => void;
  };
  renderReturnType: void;
};
