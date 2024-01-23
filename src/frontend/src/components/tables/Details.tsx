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
import {
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconGridDots,
  IconShoppingCartFilled,
  IconTool,
  IconWorldCode
} from '@tabler/icons-react';
import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { privateEncrypt } from 'crypto';
import React, { Suspense, useEffect, useState } from 'react';

import { api } from '../../App';
import { ApiPaths } from '../../enums/ApiEndpoints';
import { GetIcon, InvenTreeIcon } from '../../functions/icons';
import { useInstance } from '../../hooks/UseInstance';
import { apiUrl } from '../../states/ApiState';

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

function PartIcon(icon: string) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
      <InvenTreeIcon icon={icon} />
    </div>
  );
}

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
          <Tooltip label="Part is not active">
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

const testFunc = (path: any, pk: any) => {
  const [instance, setInstance] = useState({});

  const query = useSuspenseQuery({
    queryKey: ['instance', path, pk],
    queryFn: async () => {
      const url = apiUrl(path, pk);

      return api
        .get(url)
        .then((response) => {
          switch (response.status) {
            case 200:
              setInstance(response.data);
              return response.data;
            default:
              setInstance({});
              return null;
          }
        })
        .catch((error) => {
          setInstance({});
          console.error(`Error fetching instance ${url}:`, error);
          return null;
        });
    },
    refetchOnMount: true
  });

  return { instance, query };
};

function OwnerBadge({ pk, type }: { pk: any; type: string }) {
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
          console.error(`Error fetching instance ${url}:`, error);
          return null;
        });
    }
  });
  console.log('ownerdata', data, apiUrl(ApiPaths.owner_list, pk));
  return (
    <Suspense fallback={<Skeleton width={200} height={20} radius="xl" />}>
      <Badge color="dark" variant="filled">
        {data.name}
      </Badge>
    </Suspense>
  );
}

function TableStringValue({
  field_data,
  field_value,
  unit = null
}: {
  field_data: any;
  field_value: any;
  unit?: null | string;
}) {
  if (field_data.owner) {
    return <OwnerBadge pk={field_value} type="owner" />;
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
    return <></>;
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
      <td style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
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
  part,
  fields,
  partIcons = false
}: {
  part: any;
  fields: any;
  partIcons?: boolean;
}) {
  console.log(part);
  return (
    <Group>
      <Table striped>
        <tbody>
          {partIcons && (
            <tr>
              <PartIcons
                assembly={part.assembly}
                template={part.is_template}
                component={part.component}
                trackable={part.trackable}
                purchaseable={part.purchaseable}
                saleable={part.salable}
                virtual={part.virtual}
                active={part.active}
              />
            </tr>
          )}
          {fields.map((data: any, index: number) => {
            let value;
            if (Array.isArray(data)) {
              value = [];
              for (const val of data) {
                value.push(part[val.name]);
              }
            } else {
              value = part[data.name];
            }
            return (
              <TableField
                field_data={data}
                field_value={value}
                key={index}
                unit={part.units}
              />
            );
          })}
        </tbody>
      </Table>
    </Group>
  );
}
