import type {
  QueryObserverResult,
  UseQueryResult
} from '@tanstack/react-query';
import type { ReactNode } from 'react';
import type { ApiEndpoints } from '..';
import type { ModelType } from '../enums/ModelType';
import type { PathParams } from './Core';

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
  custom_model?: string;
} & InstanceRenderInterface;

export interface UseInstanceResult {
  instance: any;
  setInstance: (instance: any) => void;
  refreshInstance: () => void;
  refreshInstancePromise: () => Promise<QueryObserverResult<any, any>>;
  instanceQuery: UseQueryResult;
  isLoaded: boolean;
}

export interface useInstanceProps {
  endpoint: ApiEndpoints;
  pk?: string | number | undefined;
  hasPrimaryKey?: boolean;
  params?: any;
  pathParams?: PathParams;
  disabled?: boolean;
  defaultValue?: any;
  refetchOnMount?: boolean;
  refetchOnWindowFocus?: boolean;
  updateInterval?: number;
}

export interface RemoteInstanceProps {
  model: ModelType;
  modelUrl?: string;
  modelRenderer?: (instance: any) => ReactNode;
  pk: number;
}
