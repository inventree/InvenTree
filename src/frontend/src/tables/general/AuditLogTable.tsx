import { t } from '@lingui/core/macro';
import { Badge, Group, Paper, Stack, Table, Text } from '@mantine/core';
import { IconArrowRight } from '@tabler/icons-react';
import type { DataTableRowExpansionProps } from 'mantine-datatable';
import { type ReactNode, useMemo } from 'react';
import { type NavigateFunction, useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { formatDecimal } from '@lib/functions/Formatting';
import { getDetailUrl } from '@lib/functions/Navigation';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { RenderInlineModel } from '../../components/render/Instance';
import { RenderUser } from '../../components/render/User';
import { DateColumn } from '../../components/tables/ColumnRenderers';
import {
  MaxDateFilter,
  MinDateFilter,
  UserFilter
} from '../../components/tables/Filter';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { useFilters } from '../../hooks/UseFilter';
import { useUserState } from '../../states/UserState';

// Action codes, as defined by django-auditlog
enum AuditAction {
  CREATE = 0,
  UPDATE = 1,
  DELETE = 2,
  ACCESS = 3
}

// A single field change, as returned by the 'changes_detail' API field
type AuditChange = {
  field: string;
  label: string;
  type: 'value' | 'fk' | 'm2m';
  old?: any;
  new?: any;
  old_display?: string | null;
  new_display?: string | null;
  model_type?: string | null;
  operation?: string | null;
  objects?: string[] | null;
  numeric?: boolean;
};

// Maximum number of changes rendered inline (the remainder are shown when the row is expanded)
const MAX_INLINE_CHANGES = 3;

// Maximum length of a single rendered value
const MAX_VALUE_LENGTH = 100;

/**
 * Convert a server-side model label ('app_label.model') to a frontend ModelType (if known)
 */
function resolveModelType(label?: string | null): ModelType | undefined {
  const name = label?.split('.').pop();

  if (name && name in ModelInformationDict) {
    return name as ModelType;
  }

  return undefined;
}

function actionLabel(action: AuditAction): string {
  switch (action) {
    case AuditAction.CREATE:
      return t`Created`;
    case AuditAction.UPDATE:
      return t`Updated`;
    case AuditAction.DELETE:
      return t`Deleted`;
    default:
      return t`Accessed`;
  }
}

function actionColor(action: AuditAction): string {
  switch (action) {
    case AuditAction.CREATE:
      return 'green';
    case AuditAction.UPDATE:
      return 'blue';
    case AuditAction.DELETE:
      return 'red';
    default:
      return 'gray';
  }
}

/**
 * Render a single recorded value (old or new) for a field change
 */
function AuditValue({
  value,
  display,
  modelType,
  numeric,
  navigate
}: Readonly<{
  value: any;
  display?: string | null;
  modelType?: string | null;
  numeric?: boolean;
  navigate: NavigateFunction;
}>): ReactNode {
  if (value === null || value === undefined || value === '') {
    return (
      <Text size='sm' c='dimmed' fs='italic'>
        {t`None`}
      </Text>
    );
  }

  let text: string;

  if (display) {
    text = display;
  } else if (numeric && Number.isFinite(Number(value))) {
    // Numeric values (decimals are recorded as strings, e.g. '10.00000')
    text = String(formatDecimal(Number(value)));
  } else if (typeof value === 'boolean') {
    text = value ? t`Yes` : t`No`;
  } else if (typeof value === 'object') {
    text = JSON.stringify(value);
  } else {
    text = String(value);
  }

  if (text.length > MAX_VALUE_LENGTH) {
    text = `${text.slice(0, MAX_VALUE_LENGTH)}...`;
  }

  // Link to related objects (only if the server resolved a display value)
  const relatedType = resolveModelType(modelType);

  if (display && relatedType) {
    return (
      <RenderInlineModel
        primary={text}
        url={getDetailUrl(relatedType, value)}
        navigate={navigate}
      />
    );
  }

  return <Text size='sm'>{text}</Text>;
}

/**
 * Render a single field change
 */
function AuditChangeItem({
  change,
  action,
  navigate
}: Readonly<{
  change: AuditChange;
  action: AuditAction;
  navigate: NavigateFunction;
}>): ReactNode {
  if (change.type === 'm2m') {
    const added = change.operation === 'add';

    return (
      <Group gap='xs' wrap='nowrap'>
        <Text size='sm' fw={500}>
          {change.label}:
        </Text>
        <Badge size='xs' color={added ? 'green' : 'red'}>
          {added ? t`Added` : t`Removed`}
        </Badge>
        <Text size='sm'>
          {change.objects ? change.objects.join(', ') : t`Hidden`}
        </Text>
      </Group>
    );
  }

  const newValue = (
    <AuditValue
      value={change.new}
      display={change.new_display}
      modelType={change.model_type}
      numeric={change.numeric}
      navigate={navigate}
    />
  );

  return (
    <Group gap='xs' wrap='nowrap'>
      <Text size='sm' fw={500}>
        {change.label}:
      </Text>
      {action == AuditAction.UPDATE && (
        <>
          <AuditValue
            value={change.old}
            display={change.old_display}
            modelType={change.model_type}
            numeric={change.numeric}
            navigate={navigate}
          />
          <IconArrowRight size={14} />
        </>
      )}
      {newValue}
    </Group>
  );
}

/**
 * Return the list of changes to display for an audit entry
 */
function getChanges(record: any): AuditChange[] {
  const changes: AuditChange[] = record?.changes_detail ?? [];

  if (record?.action == AuditAction.CREATE) {
    // For new objects, empty fields are not interesting
    return changes.filter(
      (change) =>
        change.type == 'm2m' ||
        !(change.new === null || change.new === undefined || change.new === '')
    );
  }

  return changes;
}

/**
 * Return a human readable label for an event delta key (e.g. 'sales_order' -> 'Sales order')
 */
function deltaLabel(key: string): string {
  // Labels for commonly used delta keys (e.g. stock tracking events)
  const labels: Record<string, string> = {
    added: t`Added`,
    build_order: t`Build Order`,
    buildorder: t`Build Order`,
    customer: t`Customer`,
    location: t`Location`,
    part: t`Part`,
    purchaseorder: t`Purchase Order`,
    quantity: t`Quantity`,
    removed: t`Removed`,
    returnorder: t`Return Order`,
    salesorder: t`Sales Order`,
    stockitem: t`Stock Item`,
    transferorder: t`Transfer Order`
  };

  if (key in labels) {
    return labels[key];
  }

  const label = key.replaceAll('_', ' ');
  return label.charAt(0).toUpperCase() + label.slice(1);
}

/**
 * Render the deltas and notes recorded against a named event (if any)
 */
function AuditEventDetails({
  record,
  navigate
}: Readonly<{
  record: any;
  navigate: NavigateFunction;
}>): ReactNode {
  const deltas: [string, any][] = Object.entries(record.deltas ?? {});

  if (deltas.length == 0 && !record.notes) {
    return null;
  }

  return (
    <Stack gap={2}>
      {deltas.map(([key, value]) => {
        // A reference to another object: {model_type, pk, str}
        const isReference =
          value !== null && typeof value === 'object' && 'model_type' in value;

        return (
          <Group key={key} gap='xs' wrap='nowrap'>
            <Text size='sm' fw={500}>
              {deltaLabel(key)}:
            </Text>
            {isReference && !value.str ? (
              <Text size='sm' c='dimmed' fs='italic'>{t`Hidden`}</Text>
            ) : (
              <AuditValue
                value={isReference ? value.pk : value}
                display={isReference ? value.str : undefined}
                modelType={isReference ? value.model_type : undefined}
                numeric={typeof value === 'number'}
                navigate={navigate}
              />
            )}
          </Group>
        );
      })}
      {record.notes && (
        <Text size='sm' fs='italic'>
          {record.notes}
        </Text>
      )}
    </Stack>
  );
}

/**
 * Render a summary of the changes for an audit entry
 */
function AuditChangesSummary({
  record,
  navigate
}: Readonly<{
  record: any;
  navigate: NavigateFunction;
}>): ReactNode {
  const eventDetails = (
    <AuditEventDetails record={record} navigate={navigate} />
  );

  if (record.action == AuditAction.DELETE) {
    // A named event may be recorded against the deletion (e.g. stock depleted to zero)
    return (
      <Stack gap={2}>
        {eventDetails}
        <Text size='sm' c='dimmed' fs='italic'>
          {t`Object was deleted`}
        </Text>
      </Stack>
    );
  }

  const changes = getChanges(record);

  if (changes.length == 0) {
    // A named event may be recorded without any field changes
    if (record.event_type !== null && record.event_type !== undefined) {
      return eventDetails;
    }

    return (
      <Text size='sm' c='dimmed' fs='italic'>
        {t`No changes recorded`}
      </Text>
    );
  }

  return (
    <Stack gap={2}>
      {eventDetails}
      {changes.slice(0, MAX_INLINE_CHANGES).map((change) => (
        <AuditChangeItem
          key={change.field}
          change={change}
          action={record.action}
          navigate={navigate}
        />
      ))}
      {changes.length > MAX_INLINE_CHANGES && (
        <Text size='xs' c='dimmed'>
          {t`+ ${changes.length - MAX_INLINE_CHANGES} more (expand row to view)`}
        </Text>
      )}
    </Stack>
  );
}

/**
 * Render a table of all changes for an audit entry (shown when a row is expanded)
 */
function AuditChangesDetail({
  record,
  navigate
}: Readonly<{
  record: any;
  navigate: NavigateFunction;
}>): ReactNode {
  const changes = getChanges(record);
  const showOld = record.action != AuditAction.CREATE;
  const showNew = record.action != AuditAction.DELETE;

  return (
    <Paper p='xs' withBorder>
      <Table striped withColumnBorders>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{t`Field`}</Table.Th>
            {showOld && <Table.Th>{t`Old Value`}</Table.Th>}
            {showNew && <Table.Th>{t`New Value`}</Table.Th>}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {changes.map((change) => (
            <Table.Tr key={change.field}>
              <Table.Td>
                <Text size='sm' fw={500}>
                  {change.label}
                </Text>
              </Table.Td>
              {change.type == 'm2m' ? (
                <Table.Td colSpan={showOld && showNew ? 2 : 1}>
                  <AuditChangeItem
                    change={change}
                    action={record.action}
                    navigate={navigate}
                  />
                </Table.Td>
              ) : (
                <>
                  {showOld && (
                    <Table.Td>
                      <AuditValue
                        value={change.old}
                        display={change.old_display}
                        modelType={change.model_type}
                        numeric={change.numeric}
                        navigate={navigate}
                      />
                    </Table.Td>
                  )}
                  {showNew && (
                    <Table.Td>
                      <AuditValue
                        value={change.new}
                        display={change.new_display}
                        modelType={change.model_type}
                        numeric={change.numeric}
                        navigate={navigate}
                      />
                    </Table.Td>
                  )}
                </>
              )}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Paper>
  );
}

/**
 * Table for displaying audit log (change history) entries.
 *
 * - When modelType and modelId are provided, displays the history of a single object
 *   (including changes to its child objects, unless includeChildren is false)
 * - When only modelType is provided, displays the history of all objects of that type
 * - Otherwise, displays all audit log entries visible to the user
 */
export function AuditLogTable({
  modelType,
  modelId,
  includeChildren
}: Readonly<{
  modelType?: ModelType;
  modelId?: number | string;
  includeChildren?: boolean;
}>): ReactNode {
  const navigate = useNavigate();
  const user = useUserState();

  const table = useTable(modelType ? `audit-log-${modelType}` : 'audit-log');

  const singleObject = modelType !== undefined && modelId !== undefined;

  // Model type choices are provided via the OPTIONS metadata for the list endpoint
  const modelTypeFilters = useFilters({
    url: apiUrl(ApiEndpoints.audit_log_list),
    method: 'OPTIONS',
    accessor: 'data.filters.model_type.choices',
    transform: (item: any) => ({
      value: item.value,
      label: item.display_name
    }),
    // Not required if the table is restricted to a particular model type
    enabled: !modelType
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'action',
        label: t`Action`,
        description: t`Filter by action type`,
        type: 'choice',
        choices: [
          { value: `${AuditAction.CREATE}`, label: t`Created` },
          { value: `${AuditAction.UPDATE}`, label: t`Updated` },
          { value: `${AuditAction.DELETE}`, label: t`Deleted` }
        ]
      },
      UserFilter({
        name: 'actor',
        label: t`User`,
        description: t`Filter by the user who made the change`
      }),
      MinDateFilter(),
      MaxDateFilter()
    ];

    if (!modelType) {
      filters.push({
        name: 'model_type',
        label: t`Model Type`,
        description: t`Filter by the type of item which was changed`,
        type: 'choice',
        choices: modelTypeFilters.choices
      });
    }

    if (singleObject && includeChildren === undefined) {
      filters.push({
        name: 'include_children',
        label: t`Include Related`,
        description: t`Include changes to related items (e.g. line items)`,
        type: 'boolean'
      });
    }

    return filters;
  }, [singleObject, includeChildren, modelType, modelTypeFilters.choices]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      DateColumn({
        accessor: 'timestamp',
        title: t`Date`,
        switchable: false,
        extra: { showTime: true }
      }),
      {
        accessor: 'action',
        title: t`Action`,
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <Badge color={actionColor(record.action)} variant='light'>
            {record.event_label ?? actionLabel(record.action)}
          </Badge>
        )
      },
      {
        accessor: 'object_repr',
        title: t`Item`,
        sortable: false,
        switchable: true,
        render: (record: any) => {
          const objectType = resolveModelType(record.model_type);
          const typeLabel = objectType
            ? ModelInformationDict[objectType].label()
            : (record.model_label ?? record.model_type);

          // Deleted objects no longer have a detail page
          const url =
            objectType && record.action != AuditAction.DELETE
              ? getDetailUrl(objectType, record.object_pk)
              : undefined;

          return (
            <Stack gap={0}>
              <RenderInlineModel
                primary={record.object_repr}
                url={url}
                navigate={navigate}
              />
              <Text size='xs' c='dimmed'>
                {typeLabel}
              </Text>
            </Stack>
          );
        }
      },
      {
        accessor: 'changes',
        title: t`Changes`,
        sortable: false,
        switchable: false,
        render: (record: any) => (
          <AuditChangesSummary record={record} navigate={navigate} />
        )
      },
      {
        accessor: 'actor',
        title: t`User`,
        sortable: true,
        switchable: true,
        render: (record: any) => {
          if (record.actor_detail) {
            return RenderUser({ instance: record.actor_detail });
          }

          // The user account has since been deleted
          if (record.actor_username) {
            return (
              <Text size='sm' c='dimmed'>
                {t`${record.actor_username} (deleted)`}
              </Text>
            );
          }

          if (record.additional_data?.source) {
            return (
              <Text size='sm' c='dimmed' fs='italic'>
                {record.additional_data.source}
              </Text>
            );
          }

          return <Text size='sm' c='dimmed' fs='italic'>{t`System`}</Text>;
        }
      },
      {
        accessor: 'remote_addr',
        title: t`IP Address`,
        sortable: false,
        switchable: true,
        defaultVisible: false,
        // Only returned by the API for staff users
        hidden: !user.isStaff()
      }
    ];
  }, [navigate, user]);

  const rowExpansion: DataTableRowExpansionProps<any> = useMemo(() => {
    return {
      allowMultiple: true,
      expandable: ({ record }: { record: any }) =>
        record.action != AuditAction.DELETE && getChanges(record).length > 0,
      content: ({ record }: { record: any }) => (
        <AuditChangesDetail record={record} navigate={navigate} />
      )
    };
  }, [navigate]);

  return (
    <InvenTreeTable
      tableState={table}
      url={apiUrl(ApiEndpoints.audit_log_list)}
      columns={tableColumns}
      props={{
        params: {
          model_type: modelType,
          model_id: modelId,
          include_children: includeChildren,
          changes_detail: true,
          actor_detail: true
        },
        tableFilters: tableFilters,
        rowExpansion: rowExpansion,
        noRecordsText: t`No history found`
      }}
    />
  );
}
