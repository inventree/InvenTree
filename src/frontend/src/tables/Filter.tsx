import { t } from '@lingui/macro';

import type { ModelType } from '../enums/ModelType';
import { useGlobalStatusState } from '../states/StatusState';

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
 */
export type TableFilterType = 'boolean' | 'choice' | 'date' | 'text';

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
  type?: TableFilterType;
  choices?: TableFilterChoice[];
  choiceFunction?: () => TableFilterChoice[];
  defaultValue?: any;
  value?: any;
  displayValue?: any;
  active?: boolean;
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
    const statusCodeList = useGlobalStatusState.getState().status;

    if (!statusCodeList) {
      return [];
    }

    const codes = statusCodeList[model];

    if (codes) {
      return Object.keys(codes).map((key) => {
        const entry = codes[key];
        return {
          value: entry.key.toString(),
          label: entry.label?.toString() ?? entry.key.toString()
        };
      });
    }

    return [];
  };
}

// Define some commonly used filters

export function AssignedToMeFilter(): TableFilter {
  return {
    name: 'assigned_to_me',
    type: 'boolean',
    label: t`Assigned to me`,
    description: t`Show orders assigned to me`
  };
}

export function OutstandingFilter(): TableFilter {
  return {
    name: 'outstanding',
    label: t`Outstanding`,
    description: t`Show outstanding items`
  };
}

export function OverdueFilter(): TableFilter {
  return {
    name: 'overdue',
    label: t`Overdue`,
    description: t`Show overdue items`
  };
}

export function MinDateFilter(): TableFilter {
  return {
    name: 'min_date',
    label: t`Minimum Date`,
    description: t`Show items after this date`,
    type: 'date'
  };
}

export function MaxDateFilter(): TableFilter {
  return {
    name: 'max_date',
    label: t`Maximum Date`,
    description: t`Show items before this date`,
    type: 'date'
  };
}

export function CreatedBeforeFilter(): TableFilter {
  return {
    name: 'created_before',
    label: t`Created Before`,
    description: t`Show items created before this date`,
    type: 'date'
  };
}

export function CreatedAfterFilter(): TableFilter {
  return {
    name: 'created_after',
    label: t`Created After`,
    description: t`Show items created after this date`,
    type: 'date'
  };
}

export function TargetDateBeforeFilter(): TableFilter {
  return {
    name: 'target_date_before',
    label: t`Target Date Before`,
    description: t`Show items with a target date before this date`,
    type: 'date'
  };
}

export function TargetDateAfterFilter(): TableFilter {
  return {
    name: 'target_date_after',
    label: t`Target Date After`,
    description: t`Show items with a target date after this date`,
    type: 'date'
  };
}

export function CompletedBeforeFilter(): TableFilter {
  return {
    name: 'completed_before',
    label: t`Completed Before`,
    description: t`Show items completed before this date`,
    type: 'date'
  };
}

export function CompletedAfterFilter(): TableFilter {
  return {
    name: 'completed_after',
    label: t`Completed After`,
    description: t`Show items completed after this date`,
    type: 'date'
  };
}

export function HasProjectCodeFilter(): TableFilter {
  return {
    name: 'has_project_code',
    type: 'boolean',
    label: t`Has Project Code`,
    description: t`Show orders with an assigned project code`
  };
}
