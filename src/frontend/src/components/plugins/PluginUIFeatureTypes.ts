import { InvenTreeIconType } from '../../functions/icons';
import { TemplateI } from '../../tables/settings/TemplateTable';
import { InvenTreeContext } from './PluginContext';

// #region  Type Helpers
export type BaseUIFeature = {
  featureType: string;
  requestContext: Record<string, any>;
  responseOptions: Record<string, any>;
  renderContext: Record<string, any>;
};

export type PluginUIGetFeatureType<T extends BaseUIFeature> = (
  ref: HTMLDivElement,
  params: {
    renderContext: T['renderContext'];
    inventreeContext: InvenTreeContext;
  }
) => void;

export type PluginUIFuncWithoutInvenTreeContextType<T extends BaseUIFeature> = (
  ref: HTMLDivElement,
  renderContext: T['renderContext']
) => void;

export type PluginUIFeatureAPIResponse<T extends BaseUIFeature> = {
  feature_type: T['featureType'];
  options: T['responseOptions'];
  source: string;
};

// #region Types
export type TemplateEditorUIFeature = {
  featureType: 'template_editor';
  requestContext: {
    template_type: string;
    template_model: string;
  };
  responseOptions: {
    key: string;
    title: string;
    icon: InvenTreeIconType;
  };
  renderContext: {
    registerHandlers: (params: {
      setCode: (code: string) => void;
      getCode: () => string;
    }) => void;
    template: TemplateI;
  };
};

export type TemplatePreviewUIFeature = {
  featureType: 'template_preview';
  requestContext: {
    template_type: string;
    template_model: string;
  };
  responseOptions: {
    key: string;
    title: string;
    icon: InvenTreeIconType;
  };
  renderContext: {
    template: TemplateI;
  };
};
