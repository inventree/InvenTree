import { t } from '@lingui/macro';
import type { ModelType } from '../../enums/ModelType';

/**
 * Interface for the table filter choice
 */
export type TableFilterChoice = {
  value: string;
  label: string;
};

/**
 * Available filter types
 *
 * boolean: A simple true/false filter
 * choice: A filter which allows selection from a list of (supplied)
 * date: A filter which allows selection from a date input
 * text: A filter which allows raw text input
 * api: A filter which fetches its options from an API endpoint
 */
export type TableFilterType = 'boolean' | 'choice' | 'date' | 'text' | 'api';

/**
 * Interface for the table filter type. Provides a number of options for selecting filter value:
 *
 * name: The name of the filter (used for query string)
 * label: The label to display in the UI (human readable)
 * description: A description of the filter (human readable)
 * type: The type of filter (see TableFilterType)
 * choices: A list of TableFilterChoice objects
 * choiceFunction: A function which returns a list of TableFilterChoice objects
 * defaultValue: The default value for the filter
 * value: The current value of the filter
 * displayValue: The current display value of the filter
 * active: Whether the filter is active (false = hidden, not used)
 * apiUrl: The API URL to use for fetching dynamic filter options
 * model: The model type to use for fetching dynamic filter options
 * modelRenderer: A function to render a simple text version of the model type
 */
export type TableFilter = {
  name: string;
  label: string;
  description?: string;
  type?: TableFilterType;
  choices?: TableFilterChoice[];
  choiceFunction?: () => TableFilterChoice[];
  defaultValue?: any;
  value?: any;
  displayValue?: any;
  active?: boolean;
  apiUrl?: string;
  model?: ModelType;
  modelRenderer?: (instance: any) => string;
};

// Determine the filter "type" - if it is not supplied
export function getFilterType(filter: TableFilter): TableFilterType {
  if (filter.type) {
    return filter.type;
  } else if (filter.apiUrl && filter.model) {
    return 'api';
  } else if (filter.choices || filter.choiceFunction) {
    return 'choice';
  } else {
    return 'boolean';
  }
}

/**
 * Return list of available filter options for a given filter
 * @param filter - TableFilter object
 * @returns - A list of TableFilterChoice objects
 */
export function getTableFilterOptions(
  filter: TableFilter
): TableFilterChoice[] {
  if (filter.choices) {
    return filter.choices;
  }

  if (filter.choiceFunction) {
    return filter.choiceFunction();
  }

  // Default fallback is a boolean filter
  return [
    { value: 'true', label: t`Yes` },
    { value: 'false', label: t`No` }
  ];
}
