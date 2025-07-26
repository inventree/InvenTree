import type { ModelType } from '../enums/ModelType';

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
 * apiFilter: Optional filters to apply when fetching options from the API
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
  apiFilter?: Record<string, any>;
  model?: ModelType;
  modelRenderer?: (instance: any) => string;
};

/*
 * Type definition for representing the state of a group of filters.
 * These may be applied to a data view (e.g. table, calendar) to filter the displayed data.
 *
 * filterKey: A unique key for the filter set
 * activeFilters: An array of active filters
 * setActiveFilters: A function to set the active filters
 * clearActiveFilters: A function to clear all active filters
 */
export type FilterSetState = {
  filterKey: string;
  activeFilters: TableFilter[];
  setActiveFilters: (filters: TableFilter[]) => void;
  clearActiveFilters: () => void;
};
