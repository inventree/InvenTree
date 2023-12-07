import { t } from '@lingui/macro';

import { ModelType } from '../../enums/ModelType';
import { useServerApiState } from '../../states/ApiState';

/**
 * Interface for the table filter choice
 */
export type TableFilterChoice = {
  value: string;
  label: string;
};

/**
 * Interface for the table filter type. Provides a number of options for selecting filter value:
 *
 * choices: A list of TableFilterChoice objects
 * choiceFunction: A function which returns a list of TableFilterChoice objects
 * statusType: A ModelType which is used to generate a list of status codes
 */
export type TableFilter = {
  name: string;
  label: string;
  description?: string;
  type?: string;
  choices?: TableFilterChoice[];
  choiceFunction?: () => TableFilterChoice[];
  defaultValue?: any;
  value?: any;
};

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

/*
 * Construct a table filter which allows filtering by status code
 */
export function StatusFilterOptions(
  model: ModelType
): () => TableFilterChoice[] {
  return () => {
    const statusCodeList = useServerApiState.getState().status;

    if (!statusCodeList) {
      return [];
    }

    const codes = statusCodeList[model];

    if (codes) {
      return Object.keys(codes).map((key) => {
        const entry = codes[key];
        return {
          value: entry.key,
          label: entry.label ?? entry.key
        };
      });
    }

    return [];
  };
}

export function AssignedToMeFilter(): TableFilter {
  return {
    name: 'assigned_to_me',
    label: t`Assigned to me`,
    description: t`Show orders assigned to me`
  };
}

export function OutstandingFilter(): TableFilter {
  return {
    name: 'outstanding',
    label: t`Outstanding`,
    description: t`Show outstanding orders`
  };
}

export function OverdueFilter(): TableFilter {
  return {
    name: 'overdue',
    label: t`Overdue`,
    description: t`Show overdue orders`
  };
}
