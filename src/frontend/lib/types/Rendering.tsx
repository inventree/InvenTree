import type { ModelType } from '../enums/ModelType';

/**
 * Interface for rendering a model instance.
 */
export interface InstanceRenderInterface {
  instance: any;
  link?: boolean;
  navigate?: any;
  showSecondary?: boolean;
  extra?: Record<string, any>;
}

type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
};

export type ModelRendererDict = EnumDictionary<
  ModelType,
  (props: Readonly<InstanceRenderInterface>) => React.ReactNode
>;

export type RenderInstanceProps = {
  model: ModelType | undefined;
} & InstanceRenderInterface;
