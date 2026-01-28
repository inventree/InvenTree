import { t } from '@lingui/core/macro';
import {
  Anchor,
  Avatar,
  Badge,
  Group,
  HoverCard,
  type MantineColor,
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

import { ProgressBar } from '@lib/components/ProgressBar';
import { YesNoButton } from '@lib/components/YesNoButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getBaseUrl, getDetailUrl } from '@lib/functions/Navigation';
import { navigateToLink } from '@lib/functions/Navigation';
import type { InvenTreeIconType } from '@lib/types/Icons';
import { useApi } from '../../contexts/ApiContext';
import { formatDate, formatDecimal } from '../../defaults/formatters';
import { InvenTreeIcon } from '../../functions/icons';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { CopyButton } from '../buttons/CopyButton';
import { StylishText } from '../items/StylishText';
import { getModelInfo } from '../render/ModelType';
import { StatusRenderer } from '../render/StatusRenderer';

export type DetailsField = {
  hidden?: boolean;
  icon?: keyof InvenTreeIconType;
  name: string;
  label?: string;
  badge?: BadgeType;
  copy?: boolean;
  value_formatter?: () => ValueFormatterReturn;
} & (
  | NumberDetailField
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

type NumberDetailField = {
  type: 'number';
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

function HoverNameBadge(data: any, type: BadgeType) {
  function lines(data: any) {
    switch (type) {
      case 'owner':
        return [
          `${data.label}: ${data.name}`,
          data.name,
          getDetailUrl(data.owner_model, data.owner_id, true),
          undefined,
          undefined
        ];
      case 'user':
        return [
          `${data.first_name} ${data.last_name}`,
          data.username,
          getDetailUrl(ModelType.user, data.pk, true),
          data?.image,
          <>
            {data.is_superuser && <Badge color='red'>{t`Superuser`}</Badge>}
            {data.is_staff && <Badge color='blue'>{t`Staff`}</Badge>}
            {data.email && t`Email: ` + data.email}
          </>
        ];
      case 'group':
        return [
          data.name,
          data.name,
          getDetailUrl(ModelType.group, data.pk, true),
          data?.image,
          undefined
        ];
      default:
        return 'dd';
    }
  }
  const line_data = lines(data);
  return (
    <HoverCard.Dropdown>
      <Group>
        <Avatar src={line_data[3]} radius='xl' />
        <Stack gap={5}>
          <Text size='sm' fw={700} style={{ lineHeight: 1 }}>
            {line_data[0]}
          </Text>
          <Anchor
            href={line_data[2]}
            c='dimmed'
            size='xs'
            style={{ lineHeight: 1 }}
          >
            {line_data[1]}
          </Anchor>
        </Stack>
      </Group>

      <Text size='sm' mt='md'>
        {line_data[4]}
      </Text>
    </HoverCard.Dropdown>
  );
}

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

      return api.get(url).then((response) => {
        switch (response.status) {
          case 200:
            return response.data;
          default:
            return {};
        }
      });
    }
  });

  const settings = useGlobalSettingsState();
  const nameComp = useMemo(() => {
    if (!data) return <Skeleton height={12} radius='md' />;
    return HoverNameBadge(data, type);
  }, [data]);

  if (!data || data.isLoading || data.isFetching) {
    return <Skeleton height={12} radius='md' />;
  }

  // Rendering a user's name for the badge
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
        <HoverCard
          width={320}
          shadow='md'
          withArrow
          openDelay={200}
          closeDelay={400}
        >
          <HoverCard.Target>
            <p>{data?.name ?? _render_name()}</p>
          </HoverCard.Target>
          {nameComp}
        </HoverCard>
      </Badge>
      <InvenTreeIcon icon={type === 'user' ? type : data.label} />
    </Group>
  );
}

function DateValue(props: Readonly<FieldProps>) {
  return <Text size='sm'>{formatDate(props.field_value?.toString())}</Text>;
}

// Return a formatted "number" value, with optional unit
function NumberValue(props: Readonly<FieldProps>) {
  const value = props?.field_value;

  // Convert to double
  const numberValue = Number.parseFloat(value.toString());

  if (value === null || value === undefined) {
    return <Text size='sm'>'---'</Text>;
  }

  return (
    <Group wrap='nowrap' gap='xs' justify='left'>
      <Text size='sm'>{formatDecimal(numberValue)}</Text>
      {!!props.field_data?.unit && (
        <Text size='xs'>[{props.field_data?.unit}]</Text>
      )}
    </Group>
  );
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

  const absoluteUrl = useMemo(() => {
    return `/${getBaseUrl()}${detailUrl}`;
  }, [detailUrl]);

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

  let color: MantineColor | undefined = undefined;

  if (value === undefined) {
    value = data?.name ?? props.field_data?.backup_value ?? t`No name defined`;
    make_link = false;
    color = 'red';
  }

  return (
    <>
      {make_link ? (
        <Anchor href={absoluteUrl} onClick={handleLinkClick}>
          <Text>{value}</Text>
        </Anchor>
      ) : (
        <Text c={color}>{value}</Text>
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
      size='lg'
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
      case 'number':
        return NumberValue;
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
            icon={field.icon ?? (field.name as keyof InvenTreeIconType)}
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
  const visibleFields = useMemo(() => {
    return fields.filter((field) => !field.hidden);
  }, [fields]);

  if (!visibleFields?.length) {
    return <div />;
  }

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
            {visibleFields.map((field: DetailsField, index: number) => (
              <DetailsTableField field={field} item={item} key={index} />
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Paper>
  );
}
