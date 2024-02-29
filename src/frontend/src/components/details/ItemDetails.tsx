import { Grid, Group, Paper, SimpleGrid } from '@mantine/core';
import React from 'react';

import { UserRoles } from '../../enums/Roles';
import { DetailsField, DetailsTable } from '../../tables/Details';
import { DetailImageButtonProps, DetailsImage } from './DetailsImage';

/**
 * Type for defining field arrays
 */
export type ItemDetailFields = {
  left: DetailsField[][];
  right?: DetailsField[][];
  bottom_left?: DetailsField[][];
  bottom_right?: DetailsField[][];
  image?: DetailsImageType;
};

/**
 * Type for defining details image
 */
export type DetailsImageType = {
  name: string;
  imageActions: DetailImageButtonProps;
};

export function ItemDetailsGrid(props: React.PropsWithChildren<{}>) {
  return (
    <Paper p="xs">
      <SimpleGrid cols={2} spacing="xs" verticalSpacing="xs">
        {props.children}
      </SimpleGrid>
    </Paper>
  );
}

/**
 * Render a Details panel of the given model
 * @param params Object with the data of the model to render
 * @param apiPath Path to use for image updating
 * @param refresh useInstance refresh method to refresh when making updates
 * @param fields Object with all field sections
 * @param partModel set to true only if source model is Part
 */
export function ItemDetails({
  appRole,
  params = {},
  apiPath,
  refresh,
  fields,
  partModel = false
}: {
  appRole: UserRoles;
  params?: any;
  apiPath: string;
  refresh: () => void;
  fields: ItemDetailFields;
  partModel: boolean;
}) {
  return (
    <Paper p="xs">
      <SimpleGrid cols={2} spacing="xs" verticalSpacing="xs">
        <Grid>
          {fields.image && (
            <Grid.Col span={4}>
              <DetailsImage
                appRole={appRole}
                imageActions={fields.image.imageActions}
                src={params.image}
                apiPath={apiPath}
                refresh={refresh}
                pk={params.pk}
              />
            </Grid.Col>
          )}
          <Grid.Col span={8}>
            {fields.left && (
              <DetailsTable
                item={params}
                fields={fields.left}
                partIcons={partModel}
              />
            )}
          </Grid.Col>
        </Grid>
        {fields.right && <DetailsTable item={params} fields={fields.right} />}
        {fields.bottom_left && (
          <DetailsTable item={params} fields={fields.bottom_left} />
        )}
        {fields.bottom_right && (
          <DetailsTable item={params} fields={fields.bottom_right} />
        )}
      </SimpleGrid>
    </Paper>
  );
}
