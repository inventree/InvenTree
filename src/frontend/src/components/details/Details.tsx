import { t } from '@lingui/macro';
import {
  Anchor,
  Badge,
  Group,
  Paper,
  Skeleton,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { getValueAtPath } from 'mantine-datatable';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { useApi } from '../../contexts/ApiContext';
import { formatDate } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import type { ModelType } from '../../enums/ModelType';
import { InvenTreeIcon, type InvenTreeIconType } from '../../functions/icons';
import { navigateToLink } from '../../functions/navigation';
import { getDetailUrl } from '../../functions/urls';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { CopyButton } from '../buttons/CopyButton';
import { YesNoButton } from '../buttons/YesNoButton';
import { ProgressBar } from '../items/ProgressBar';
import { StylishText } from '../items/StylishText';
import { getModelInfo } from '../render/ModelType';
import { StatusRenderer } from '../render/StatusRenderer';

export type DetailsField = {
  hidden?: boolean;
  icon?: InvenTreeIconType;
  name: string;
  label?: string;
  badge?: BadgeType;
  copy?: boolean;
  value_formatter?: () => ValueFormatterReturn;
} & (
  | StringDetailField
  | BooleanField
  | LinkDetailField
  | ProgressBarField
  | StatusField
);

type BadgeType = 'owner' | 'user' | 'group';
type ValueFormatterReturn = string | number | null | React.ReactNode;

type StringDetailField = {
  type: 'string' | 'text' | 'date';
  unit?: boolean;
};

type BooleanField = {
  type: 'boolean';
};

type LinkDetailField = {
  type: 'link';
  link?: boolean;
} & (InternalLinkField | ExternalLinkField);

type InternalLinkField = {
  model: ModelType;
  model_field?: string;
  model_formatter?: (value: any) => string;
  model_filters?: any;
  backup_value?: string;
};

type ExternalLinkField = {
  external: true;
};

type ProgressBarField = {
  type: 'progressbar';
  progress: number;
  total: number;
};

type StatusField = {
  type: 'status';
  model: ModelType;
};

type FieldProps = {
  field_data: any;
  field_value: string | number;
  unit?: string | null;
};

/**
 * Fetches user or group info from backend and formats into a badge.
 * Badge shows username, full name, or group name depending on server settings.
 * Badge appends icon to describe type of Owner
 */
function NameBadge({
  pk,
  type
}: Readonly<{ pk: string | number; type: BadgeType }>) {
  const api = useApi();

  const { data } = useQuery({
    queryKey: ['badge', type, pk],
    queryFn: async () => {
      let path = '';

      switch (type) {
        case 'owner':
          path = ApiEndpoints.owner_list;
          break;
        case 'user':
          path = ApiEndpoints.user_list;
          break;
        case 'group':
          path = ApiEndpoints.group_list;
          break;
        default:
          return {};
      }

      const url = apiUrl(path, pk);

      return api
        .get(url)
        .then((response) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return {};
          }
        })
        .catch(() => {
          return {};
        });
    }
  });

  const settings = useGlobalSettingsState();

  if (!data || data.isLoading || data.isFetching) {
    return <Skeleton height={12} radius='md' />;
  }

  // Rendering a user's rame for the badge
  function _render_name() {
    if (!data || !data.pk) {
      return '';
    } else if (type === 'user' && settings.isSet('DISPLAY_FULL_NAMES')) {
      if (data.first_name || data.last_name) {
        return `${data.first_name} ${data.last_name}`;
      } else {
        return data.username;
      }
    } else if (type === 'user') {
      return data.username;
    } else {
      return data.name;
    }
  }

  return (
    <Group wrap='nowrap' gap='sm' justify='right'>
      <Badge
        color='dark'
        variant='filled'
        style={{ display: 'flex', alignItems: 'center' }}
      >
        {data?.name ?? _render_name()}
      </Badge>
      <InvenTreeIcon icon={type === 'user' ? type : data.label} />
    </Group>
  );
}

function DateValue(props: Readonly<FieldProps>) {
  return <Text size='sm'>{formatDate(props.field_value?.toString())}</Text>;
}

/**
 * Renders the value of a 'string' or 'text' field.
 * If owner is defined, only renders a badge
 * If user is defined, a badge is rendered in addition to main value
 */
function TableStringValue(props: Readonly<FieldProps>) {
  const value = props?.field_value;

  let renderedValue = null;

  if (props.field_data?.badge) {
    return <NameBadge pk={value} type={props.field_data.badge} />;
  } else if (props?.field_data?.value_formatter) {
    renderedValue = props.field_data.value_formatter();
  } else if (value === null || value === undefined) {
    renderedValue = <Text size='sm'>'---'</Text>;
  } else {
    renderedValue = <Text size='sm'>{value.toString()}</Text>;
  }

  return (
    <Group wrap='nowrap' gap='xs' justify='space-apart'>
      <Group wrap='nowrap' gap='xs' justify='left'>
        {renderedValue}
        {props.field_data.unit && <Text size='xs'>{props.unit}</Text>}
      </Group>
      {props.field_data.user && (
        <NameBadge pk={props.field_data?.user} type='user' />
      )}
    </Group>
  );
}

function BooleanValue(props: Readonly<FieldProps>) {
  return <YesNoButton value={props.field_value} />;
}

function TableAnchorValue(props: Readonly<FieldProps>) {
  const api = useApi();
  const navigate = useNavigate();

  const { data } = useQuery({
    queryKey: ['detail', props.field_data.model, props.field_value],
    queryFn: async () => {
      if (!props.field_data?.model) {
        return {};
      }

      const modelDef = getModelInfo(props.field_data.model);

      if (!modelDef?.api_endpoint) {
        return {};
      }

      const url = apiUrl(modelDef.api_endpoint, props.field_value);

      return api
        .get(url, {
          params: props.field_data.model_filters ?? undefined
        })
        .then((response) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return {};
          }
        })
        .catch(() => {
          return {};
        });
    }
  });

  const detailUrl = useMemo(() => {
    return (
      props?.field_data?.model &&
      getDetailUrl(props.field_data.model, props.field_value)
    );
  }, [props.field_data.model, props.field_value]);

  const handleLinkClick = useCallback(
    (event: any) => {
      navigateToLink(detailUrl, navigate, event);
    },
    [detailUrl]
  );

  if (!data || data.isLoading || data.isFetching) {
    return <Skeleton height={12} radius='md' />;
  }

  if (props.field_data.external) {
    return (
      <Anchor
        href={`${props.field_value}`}
        target={'_blank'}
        rel={'noreferrer noopener'}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <Text>{props.field_value}</Text>
          <InvenTreeIcon icon='external' iconProps={{ size: 15 }} />
        </span>
      </Anchor>
    );
  }

  let make_link = props.field_data?.link ?? true;

  // Construct the "return value" for the fetched data
  let value = undefined;

  if (props.field_data.model_formatter) {
    value = props.field_data.model_formatter(data) ?? value;
  } else if (props.field_data.model_field) {
    value = data?.[props.field_data.model_field] ?? value;
  } else {
    value = data?.name;
  }

  if (value === undefined) {
    value = data?.name ?? props.field_data?.backup_value ?? t`No name defined`;
    make_link = false;
  }

  return (
    <>
      {make_link ? (
        <Anchor href='#' onClick={handleLinkClick}>
          <Text>{value}</Text>
        </Anchor>
      ) : (
        <Text>{value}</Text>
      )}
    </>
  );
}

function ProgressBarValue(props: Readonly<FieldProps>) {
  if (props.field_data.total <= 0) {
    return <Text size='sm'>{props.field_data.progress}</Text>;
  }

  return (
    <ProgressBar
      value={props.field_data.progress}
      maximum={props.field_data.total}
      progressLabel
    />
  );
}

function StatusValue(props: Readonly<FieldProps>) {
  return (
    <StatusRenderer type={props.field_data.model} status={props.field_value} />
  );
}

function CopyField({ value }: Readonly<{ value: string }>) {
  return <CopyButton value={value} />;
}

export function DetailsTableField({
  item,
  field
}: Readonly<{
  item: any;
  field: DetailsField;
}>) {
  function getFieldType(type: string) {
    switch (type) {
      case 'boolean':
        return BooleanValue;
      case 'link':
        return TableAnchorValue;
      case 'progressbar':
        return ProgressBarValue;
      case 'status':
        return StatusValue;
      case 'date':
        return DateValue;
      case 'text':
      case 'string':
      default:
        return TableStringValue;
    }
  }

  const FieldType: any = getFieldType(field.type);

  const fieldValue = useMemo(
    () => getValueAtPath(item, field.name) as string,
    [item, field.name]
  );

  return (
    <Table.Tr style={{ verticalAlign: 'top' }}>
      <Table.Td style={{ minWidth: 75, lineBreak: 'auto', flex: 2 }}>
        <Group gap='xs' wrap='nowrap'>
          <InvenTreeIcon
            icon={field.icon ?? (field.name as InvenTreeIconType)}
          />
          <Text style={{ paddingLeft: 10 }}>{field.label}</Text>
        </Group>
      </Table.Td>
      <Table.Td
        style={{
          lineBreak: 'anywhere',
          minWidth: 100,
          flex: 10,
          display: 'inline-block'
        }}
      >
        <FieldType field_data={field} field_value={fieldValue} />
      </Table.Td>
      <Table.Td style={{ width: '50' }}>
        {field.copy && <CopyField value={fieldValue} />}
      </Table.Td>
    </Table.Tr>
  );
}

export function DetailsTable({
  item,
  fields,
  title
}: Readonly<{
  item: any;
  fields: DetailsField[];
  title?: string;
}>) {
  return (
    <Paper
      p='xs'
      withBorder
      style={{ overflowX: 'hidden', width: '100%', minWidth: 200 }}
    >
      <Stack gap='xs'>
        {title && <StylishText size='lg'>{title}</StylishText>}
        <Table striped verticalSpacing={5} horizontalSpacing='sm'>
          <Table.Tbody>
            {fields
              .filter((field: DetailsField) => !field.hidden)
              .map((field: DetailsField, index: number) => (
                <DetailsTableField field={field} item={item} key={index} />
              ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Paper>
  );
}
