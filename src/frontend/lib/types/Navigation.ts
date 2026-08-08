import type { ModelType } from '../enums/ModelType';

/**
 * Navigation context carried from a table row to a detail page.
 *
 * The ids are intentionally kept as a list rather than as API query details:
 * this makes the behaviour useful for both the built-in table and plugin
 * tables, while keeping the detail page independent from table internals.
 */
export type DetailNavigationContext = {
  modelType: ModelType;
  ids: Array<string | number>;
  index: number;
};
