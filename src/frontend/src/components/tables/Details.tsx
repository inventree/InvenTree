import { Trans, t } from '@lingui/macro';
import {
  Anchor,
  Badge,
  Group,
  Skeleton,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { useSuspenseQuery } from '@tanstack/react-query';
import { Suspense } from 'react';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { InvenTreeIcon } from '../../functions/icons';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';

export type PartIconsType = {
  assembly: boolean;
  template: boolean;
  component: boolean;
  trackable: boolean;
  purchaseable: boolean;
  saleable: boolean;
  virtual: boolean;
  active: boolean;
};

export type DetailsField =
  | ({
      name: string;
      label?: string;
      owner?: boolean;
      user?: boolean;
      value_formatter?: () => (string | number)[] | string | null;
    } & (StringDetailField | LinkDetailField | ProgressBarfield))
  | DetailsField[];

type StringDetailField = {
  type: 'string' | 'text';
  unit?: boolean;
};

type LinkDetailField = {
  type: 'link';
} & (InternalLinkField | ExternalLinkField);

type InternalLinkField = {
  path: ApiPaths;
  dest: string;
};

type ExternalLinkField = {
  external: true;
};

type ProgressBarfield = {
  type: 'progressbar';
  progress: string;
  total: string;
};

/**
 * Fetches and wraps an InvenTreeIcon in a flex div
 * @param icon name of icon
 *
 */
function PartIcon(icon: string) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
      <InvenTreeIcon icon={icon} />
    </div>
  );
}

/**
 * Generates a table cell with Part icons.
 * Only used for Part Model Details
 */
function PartIcons({
  assembly,
  template,
  component,
  trackable,
  purchaseable,
  saleable,
  virtual,
  active
}: PartIconsType) {
  return (
    <td colSpan={2}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {!active && (
          <Tooltip label={t`Part is not active`}>
            <Badge color="red" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="inactive" iconProps={{ size: 19 }} />{' '}
                <Trans>Inactive</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
        {template && (
          <Tooltip
            label={t`Part is a template part (variants can be made from this part)`}
            children={PartIcon('template')}
          />
        )}
        {assembly && (
          <Tooltip
            label={t`Part can be assembled from other parts`}
            children={PartIcon('assembly')}
          />
        )}
        {component && (
          <Tooltip
            label={t`Part can be used in assemblies`}
            children={PartIcon('component')}
          />
        )}
        {trackable && (
          <Tooltip
            label={t`Part stock is tracked by serial number`}
            children={PartIcon('trackable')}
          />
        )}
        {purchaseable && (
          <Tooltip
            label={t`Part can be purchased from external suppliers`}
            children={PartIcon('purchaseable')}
          />
        )}
        {saleable && (
          <Tooltip
            label={t`Part can be sold to customers`}
            children={PartIcon('saleable')}
          />
        )}
        {virtual && (
          <Tooltip label={t`Part is virtual (not a physical part)`}>
            <Badge color="yellow" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="virtual" iconProps={{ size: 18 }} />{' '}
                <Trans>Virtual</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
      </div>
    </td>
  );
}

/**
 * Fetches user or group info from backend and formats into a badge.
 * Badge shows username, full name, or group name depending on server settings.
 * Badge appends icon to describe type of Owner
 */
function OwnerBadge({
  pk,
  type
}: {
  pk: string | number;
  type: 'user' | 'group' | 'owner';
}) {
  const { data } = useSuspenseQuery({
    queryKey: ['owner', type, pk],
    queryFn: async () => {
      let path: string = '';

      switch (type) {
        case 'owner':
          path = ApiPaths.owner_list;
          break;
        case 'user':
          path = ApiPaths.user_list;
          break;
        case 'group':
          path = ApiPaths.group_list;
          break;
      }

      const url = apiUrl(path, pk);

      return api
        .get(url)
        .then((response) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return null;
          }
        })
        .catch((error) => {
          return null;
        });
    }
  });

  const settings = useGlobalSettingsState();

  // Rendering a user's rame for the badge
  function _render_name() {
    if (type === 'user' && settings.isSet('DISPLAY_FULL_NAMES')) {
      if (data.first_name || data.last_name) {
        return `${data.first_name} ${data.last_name}`;
      }
    } else if (type === 'user') {
      return data.username;
    } else {
      return data.name;
    }
  }

  return (
    <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Badge
          color="dark"
          variant="filled"
          style={{ display: 'flex', alignItems: 'center' }}
        >
          {data.name ?? _render_name()}
        </Badge>
        <InvenTreeIcon icon={type === 'user' ? type : data.label} />
      </div>
    </Suspense>
  );
}

/**
 * Renders the value of a 'string' or 'text' field.
 * If owner is defined, only renders a badge
 * If user is defined, a badge is rendered in addition to main value
 */
function TableStringValue({
  field_data,
  field_value,
  unit = null
}: {
  field_data: any;
  field_value: string | number;
  unit?: null | string;
}) {
  if (field_data.owner) {
    return (
      <OwnerBadge pk={field_value} type={field_data.user ? 'user' : 'owner'} />
    );
  }

  if (field_data.value_formatter) {
    const data = field_data.value_formatter();
    if (true) {
      return (
        <Suspense fallback={<Skeleton width={250} height={20} />}>
          <Text>
            {data} {field_data.unit == true && unit}
          </Text>
        </Suspense>
      );
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span>
        {field_value ? field_value : field_data.unit && '0'}{' '}
        {field_data.unit == true && unit}
      </span>
      {field_data.user && <OwnerBadge pk={field_data.user} type="user" />}
    </div>
  );
}

function TableAnchorValue({
  field_data,
  field_value,
  unit = null
}: {
  field_data: any;
  field_value: any;
  unit?: null | string;
}) {
  if (field_data.external) {
    return (
      <Anchor href={field_value} target={'_blank'} rel={'noreferrer noopener'}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <Text>{field_value}</Text>
          <InvenTreeIcon icon="external" iconProps={{ size: 15 }} />
        </span>
      </Anchor>
    );
  }

  const { data } = useSuspenseQuery({
    queryKey: [field_data.path],
    queryFn: async () => {
      const url = apiUrl(field_data.path, field_value);

      return api
        .get(url)
        .then((response) => {
          switch (response.status) {
            case 200:
              return response.data;
            default:
              return null;
          }
        })
        .catch((error) => {
          console.error(`Error fetching instance ${url}:`, error);
          return null;
        });
    }
  });

  console.log('Data', data);
  return (
    <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
      <Anchor
        href={'/platform' + data.url ?? field_data.dest + field_value}
        target={data.external ? '_blank' : undefined}
        rel={data.external ? 'noreferrer noopener' : undefined}
      >
        <Text>{data.name ?? 'No name defined'}</Text>
      </Anchor>
    </Suspense>
  );
}

function TableField({
  field_data,
  field_value,
  unit = false
}: {
  field_data: any;
  field_value: any;
  unit: boolean;
}) {
  function getFieldType(type: string) {
    switch (type) {
      case 'text':
      case 'string':
        return TableStringValue;
      case 'link':
        return TableAnchorValue;
    }
  }
  let FieldType: any = null;
  if (!Array.isArray(field_data)) {
    FieldType = getFieldType(field_data.type);
  }

  return (
    <tr>
      <td style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <InvenTreeIcon
          icon={
            Array.isArray(field_data) ? field_data[0].name : field_data.name
          }
        />
        <Text>
          {Array.isArray(field_data) ? field_data[0].label : field_data.label}
        </Text>
      </td>
      <td>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {Array.isArray(field_data) ? (
            field_data.map((data: any, index: number) => {
              FieldType = getFieldType(data.type);
              return (
                <FieldType
                  field_value={field_value[index]}
                  field_data={data}
                  unit={unit}
                  key={index}
                />
              );
            })
          ) : (
            <FieldType
              field_value={field_value}
              field_data={field_data}
              unit={unit}
            />
          )}
        </div>
      </td>
    </tr>
  );
}

export function DetailsTable({
  item,
  fields,
  partIcons = false
}: {
  item: any;
  fields: any;
  partIcons?: boolean;
}) {
  return (
    <Group>
      <Table striped>
        <tbody>
          {partIcons && (
            <tr>
              <PartIcons
                assembly={item.assembly}
                template={item.is_template}
                component={item.component}
                trackable={item.trackable}
                purchaseable={item.purchaseable}
                saleable={item.salable}
                virtual={item.virtual}
                active={item.active}
              />
            </tr>
          )}
          {fields.map((data: any, index: number) => {
            let value;
            if (Array.isArray(data)) {
              value = [];
              if (data[0].value_formatter) {
                value = data[0].value_formatter();
                data[0].value_formatter = null;
                console.log('VAL', value);
              } else {
                for (const val of data) {
                  value.push(item[val.name]);
                }
              }
            } else {
              value = item[data.name];
            }
            return (
              <TableField
                field_data={data}
                field_value={value}
                key={index}
                unit={item.units}
              />
            );
          })}
        </tbody>
      </Table>
    </Group>
  );
}
