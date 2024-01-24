import { Paper } from '@mantine/core';

import { DetailImageButtonProps, DetailsImage } from '../images/DetailsImage';
import { DetailsField, DetailsTable } from '../tables/Details';

/**
 * Type for defining field arrays
 */
export type ItemDetailFields = {
  left: DetailsField[];
  right?: DetailsField[];
  bottom_left?: DetailsField[];
  bottom_right?: DetailsField[];
  image?: DetailsImageType;
};

/**
 * Type for defining details image
 */
export type DetailsImageType = {
  name: string;
  imageActions: DetailImageButtonProps;
};

/**
 * Render a Details panel of the given model
 * @param params Object with the data of the model to render
 * @param apiPath Path to use for image updating
 * @param refresh useInstance refresh method to refresh when making updates
 * @param fields Object with all field sections
 * @param partModel set to true only if source model is Part
 */
export function ItemDetails({
  params = {},
  apiPath,
  refresh,
  fields,
  partModel = false
}: {
  params?: any;
  apiPath: string;
  refresh: () => void;
  fields: ItemDetailFields;
  partModel: boolean;
}) {
  return (
    <Paper style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
      <Paper
        withBorder
        style={{ flexBasis: '49%', display: 'flex', gap: '10px' }}
      >
        {fields.image && (
          <div style={{ flexGrow: '0' }}>
            <DetailsImage
              imageActions={fields.image.imageActions}
              src={params.image}
              apiPath={apiPath}
              refresh={refresh}
              pk={params.pk}
            />
          </div>
        )}
        {fields.left && (
          <div style={{ flexGrow: '1' }}>
            <DetailsTable
              item={params}
              fields={fields.left}
              partIcons={partModel}
            />
          </div>
        )}
      </Paper>
      {fields.right && (
        <Paper style={{ flexBasis: '49%' }} withBorder>
          <DetailsTable item={params} fields={fields.right} />
        </Paper>
      )}
      {fields.bottom_left && (
        <Paper style={{ flexBasis: '49%' }} withBorder>
          <DetailsTable item={params} fields={fields.bottom_left} />
        </Paper>
      )}
      {fields.bottom_right && (
        <Paper style={{ flexBasis: '49%' }} withBorder>
          <DetailsTable item={params} fields={fields.bottom_right} />
        </Paper>
      )}
    </Paper>
  );
}
