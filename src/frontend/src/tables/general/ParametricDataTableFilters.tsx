import { t } from '@lingui/core/macro';
import { Divider, Group, Input, Select, Stack, TextInput } from '@mantine/core';
import { useEffect, useMemo, useState } from 'react';

// Define set of allowed operators for parameter filters
export const PARAMETER_FILTER_OPERATORS: Record<string, string> = {
  '=': '',
  '>': '_gt',
  '>=': '_gte',
  '<': '_lt',
  '<=': '_lte',
  '!=': '_ne',
  '~': '_icontains'
};

type ParameterFilterProps = {
  template: any;
  filters: any;
  setFilter: (templateId: number, value: string, operator: string) => void;
  clearFilter: (templateId: number, operator?: string) => void;
  closeFilter: () => void;
};

/**
 * UI element for viewing and changing boolean filter associated with a given parameter template
 */
function BooleanParameterFilter(props: ParameterFilterProps) {
  const filterValue = useMemo(() => {
    return props.filters['='] ?? '';
  }, [props.filters]);

  return (
    <Select
      aria-label={`filter-${props.template.name}`}
      data={[
        { value: 'true', label: t`True` },
        { value: 'false', label: t`False` }
      ]}
      value={filterValue}
      clearable={true}
      defaultValue={filterValue}
      onClear={() => {
        props.clearFilter(props.template.pk, '');
        props.closeFilter();
      }}
      onChange={(val) => props.setFilter(props.template.pk, val ?? '', '=')}
      placeholder={t`Select a choice`}
      clearButtonProps={{
        'aria-label': `clear-filter-${props.template.name}`
      }}
    />
  );
}

/*
 * UI element for viewing and changing choice filter associated with a given parameter template.
 * In this case, the template defines a set of choices that can be selected.
 */
function ChoiceParameterFilter(props: ParameterFilterProps) {
  const filterValue = useMemo(() => {
    return props.filters['='] ?? '';
  }, [props.filters]);

  return (
    <Select
      aria-label={`filter-${props.template.name}`}
      data={props.template.choices
        .split(',')
        .map((choice: string) => choice.trim())}
      value={filterValue}
      defaultValue={filterValue}
      onChange={(val) => props.setFilter(props.template.pk, val ?? '', '=')}
      onClear={() => {
        props.clearFilter(props.template.pk, '');
        props.closeFilter();
      }}
      clearButtonProps={{
        'aria-label': `clear-filter-${props.template.name}`
      }}
      placeholder={t`Select a choice`}
      searchable
      clearable
      // rightSection={<ClearFilterButton props={props} />}
    />
  );
}

function GenericFilterRow({
  props,
  value,
  operator,
  readonly
}: {
  props: ParameterFilterProps;
  value: string;
  operator: string;
  readonly?: boolean;
}) {
  const placeholder: string = useMemo(() => {
    let placeholder = t`Enter a value`;

    if (props.template.units) {
      placeholder += ` [${props.template.units}]`;
    }

    return placeholder;
  }, [props.template.units]);

  const [op, setOp] = useState<string>(operator);

  useEffect(() => {
    setOp(operator);
  }, [operator]);

  return (
    <Group gap='xs' wrap='nowrap'>
      <div onMouseDown={(e) => e.stopPropagation()} style={{ width: 75 }}>
        <Select
          onClick={(event) => {
            event?.stopPropagation();
          }}
          aria-label={`filter-${props.template.name}-operator`}
          data={Object.keys(PARAMETER_FILTER_OPERATORS)}
          value={op}
          searchable={false}
          clearable={false}
          defaultValue={'='}
          onChange={(value) => {
            setOp(value ?? '=');
          }}
          size='sm'
          disabled={readonly}
          width={75}
        />
      </div>
      <TextInput
        aria-label={`filter-${props.template.name}`}
        placeholder={placeholder}
        defaultValue={value}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            props.setFilter(
              props.template.pk,
              event.currentTarget.value || '',
              op
            );
            props.closeFilter();
          }
        }}
        rightSection={
          readonly && (
            <Input.ClearButton
              onClick={(event) => {
                event.stopPropagation();
                props.clearFilter(props.template.pk, op);
                props.closeFilter();
              }}
              aria-label={`clear-filter-${props.template.name}`}
            />
          )
        }
      />
    </Group>
  );
}

/*
 * In this case, the template is generic and does not have a specific type.
 * Here, the user can apply multiple filter types (e.g., '=', '<', '>')
 */
function GenericParameterFilter(props: ParameterFilterProps) {
  return (
    <Stack gap='xs'>
      {/* Render a row for each operator defined in the filters object */}
      {Object.keys(props.filters).map((operator) => {
        return (
          <GenericFilterRow
            props={props}
            value={props.filters[operator] ?? ''}
            operator={operator}
            readonly
          />
        );
      })}
      <Divider />
      {/* Render an empty row for adding a new filter */}
      <GenericFilterRow props={props} value='' operator='=' />
    </Stack>
  );
}

/**
 * UI element for viewing and changing filter(s) associated with a given parameter template
 * @param template - The parameter template object
 * @param filters - The current filters applied to the table
 * @param setFilter - Function to set a filter for the template
 * @param clearFilter - Function to clear the filter for the template
 * @param closeFilter - Function to close the filter UI
 */
export function ParameterFilter(props: ParameterFilterProps) {
  // Filter input element (depends on template type)
  return useMemo(() => {
    if (props.template.checkbox) {
      return <BooleanParameterFilter {...props} />;
    } else if (!!props.template.choices) {
      return <ChoiceParameterFilter {...props} />;
    } else {
      return <GenericParameterFilter {...props} />;
    }
  }, [props]);
}
