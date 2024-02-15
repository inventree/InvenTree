import { t } from '@lingui/macro';
import {
  ActionIcon,
  Anchor,
  CopyButton,
  Skeleton,
  Text,
  Tooltip
} from '@mantine/core';
import { useSuspenseQuery } from '@tanstack/react-query';
import { Suspense, useMemo } from 'react';

import { api } from '../../App';
import { InvenTreeIcon } from '../../functions/icons';
import { getDetailUrl } from '../../functions/urls';
import { apiUrl } from '../../states/ApiState';
import { ProgressBar } from '../items/ProgressBar';
import { getModelInfo } from '../render/ModelType';
import { DetailsField, FieldProps, FieldValueType } from './DetailsField';
import { NameBadge } from './NameBadge';

/**
 * Renders the value of a 'string' or 'text' field.
 * If owner is defined, only renders a badge
 * If user is defined, a badge is rendered in addition to main value
 */
function TableStringValue(props: FieldProps) {
  let value = props.field_value;

  if (props.field_data.value_formatter) {
    value = props.field_data.value_formatter();
  }

  if (props.field_data.badge) {
    return <NameBadge pk={value} type={props.field_data.badge} />;
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
        <span>
          {value ? value : props.field_data.unit && '0'}{' '}
          {props.field_data.unit == true && props.unit}
        </span>
      </Suspense>
      {props.field_data.user && (
        <NameBadge pk={props.field_data.user} type="user" />
      )}
    </div>
  );
}

function TableAnchorValue(props: FieldProps) {
  if (props.field_data.external) {
    return (
      <Anchor
        href={`${props.field_value}`}
        target={'_blank'}
        rel={'noreferrer noopener'}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <Text>{props.field_value}</Text>
          <InvenTreeIcon icon="external" iconProps={{ size: 15 }} />
        </span>
      </Anchor>
    );
  }

  const { data } = useSuspenseQuery({
    queryKey: ['detail', props.field_data.model, props.field_value],
    queryFn: async () => {
      const modelDef = getModelInfo(props.field_data.model);

      if (!modelDef.api_endpoint) {
        return {};
      }

      const url = apiUrl(modelDef.api_endpoint, props.field_value);

      return api
        .get(url)
        .then((response: any) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return null;
          }
        })
        .catch(() => {
          return null;
        });
    }
  });

  const detailUrl = useMemo(() => {
    return getDetailUrl(props.field_data.model, props.field_value);
  }, [props.field_data.model, props.field_value]);

  return (
    <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
      <Anchor
        href={`/platform${detailUrl}`}
        target={data?.external ? '_blank' : undefined}
        rel={data?.external ? 'noreferrer noopener' : undefined}
      >
        <Text>{data.name ?? 'No name defined'}</Text>
      </Anchor>
    </Suspense>
  );
}

function ProgressBarValue(props: FieldProps) {
  return (
    <ProgressBar
      value={props.field_data.progress}
      maximum={props.field_data.total}
      progressLabel
    />
  );
}

export function CopyField({ value }: { value: string }) {
  return (
    <CopyButton value={value}>
      {({ copied, copy }) => (
        <Tooltip label={copied ? t`Copied` : t`Copy`} withArrow>
          <ActionIcon color={copied ? 'teal' : 'gray'} onClick={copy}>
            {copied ? (
              <InvenTreeIcon icon="check" />
            ) : (
              <InvenTreeIcon icon="copy" />
            )}
          </ActionIcon>
        </Tooltip>
      )}
    </CopyButton>
  );
}

export function DetailsValue({
  field_data,
  field_value,
  unit = null
}: {
  field_data: DetailsField[];
  field_value: FieldValueType[];
  unit?: string | null;
}) {
  function getFieldType(type: string) {
    switch (type) {
      case 'text':
      case 'string':
        return TableStringValue;
      case 'link':
        return TableAnchorValue;
      case 'progressbar':
        return ProgressBarValue;
    }
  }

  return (
    <tr>
      <td
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          justifyContent: 'flex-start'
        }}
      >
        <InvenTreeIcon icon={field_data[0].name} />
        <Text>{field_data[0].label}</Text>
      </td>
      <td style={{ minWidth: '40%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              flexGrow: '1'
            }}
          >
            {field_data.map((data: DetailsField, index: number) => {
              let FieldType: any = getFieldType(data.type);
              return (
                <FieldType
                  field_data={data}
                  field_value={field_value[index]}
                  unit={unit}
                  key={index}
                />
              );
            })}
          </div>
          {field_data[0].copy && <CopyField value={`${field_value[0]}`} />}
        </div>
      </td>
    </tr>
  );
}
