import { Trans, t } from '@lingui/macro';
import {
  AspectRatio,
  Button,
  Divider,
  Group,
  Paper,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import React, { Suspense, useEffect, useState } from 'react';

import { api } from '../../App';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';

/**
 * Input props to table
 */
export type ThumbTableProps = {
  pk: string;
  limit?: number;
  offset?: number;
  search?: string;
  close: () => void;
  setImage: (image: string) => void;
};

/**
 * Data per image returned from API
 */
type ImageElement = {
  image: string;
  count: number;
};

/**
 * Input props for each thumbnail in the table
 */
type ThumbProps = {
  selected: string | null;
  element: ImageElement;
  selectImage: React.Dispatch<React.SetStateAction<string | null>>;
};

/**
 * Renders a single image thumbnail
 */
function PartThumbComponent({ selected, element, selectImage }: ThumbProps) {
  const { hovered, ref } = useHover();

  const hoverColor = 'rgba(127,127,127,0.2)';
  const selectedColor = 'rgba(127,127,127,0.29)';

  let color = '';

  if (selected === element?.image) {
    color = selectedColor;
  } else if (hovered) {
    color = hoverColor;
  }

  const src: string | undefined = element?.image
    ? `/media/${element?.image}`
    : undefined;

  return (
    <Paper
      withBorder
      style={{ backgroundColor: color }}
      p="sm"
      ref={ref}
      onClick={() => selectImage(element.image)}
    >
      <Stack justify="space-between">
        <AspectRatio ratio={1}>
          <Thumbnail size={120} src={src} align="center"></Thumbnail>
        </AspectRatio>
        <Text size="xs">
          {element.image.split('/')[1]} ({element.count})
        </Text>
      </Stack>
    </Paper>
  );
}

/**
 * Changes a part's image to the supplied URL and updates the DOM accordingly
 */
async function setNewImage(
  image: string | null,
  pk: string,
  close: () => void,
  setImage: (image: string) => void
) {
  // No need to do anything if no image is selected
  if (image === null) {
    return;
  }

  const response = await api.patch(apiUrl(ApiEndpoints.part_list, pk), {
    existing_image: image
  });

  // Update image component and close modal if update was successful
  if (response.data.image.includes(image)) {
    setImage(response.data.image);
    close();
  }
}

/**
 * Renders a "table" of thumbnails
 */
export function PartThumbTable({
  limit = 24,
  offset = 0,
  search = '',
  pk,
  close,
  setImage
}: ThumbTableProps) {
  const [img, selectImage] = useState<string | null>(null);
  const [filterInput, setFilterInput] = useState<string>('');
  const [filterQuery, setFilter] = useState<string>(search);

  // Keep search filters from updating while user is typing
  useEffect(() => {
    const timeoutId = setTimeout(() => setFilter(filterInput), 500);
    return () => clearTimeout(timeoutId);
  }, [filterInput]);

  // Fetch thumbnails from API
  const thumbQuery = useQuery({
    queryKey: [
      ApiEndpoints.part_thumbs_list,
      { limit: limit, offset: offset, search: filterQuery }
    ],
    queryFn: async () => {
      return api.get(apiUrl(ApiEndpoints.part_thumbs_list), {
        params: {
          offset: offset,
          limit: limit,
          search: filterQuery
        }
      });
    }
  });

  return (
    <>
      <Suspense>
        <Divider />
        <Paper p="sm">
          <>
            <SimpleGrid cols={8}>
              {!thumbQuery.isFetching
                ? thumbQuery.data?.data.map(
                    (data: ImageElement, index: number) => (
                      <PartThumbComponent
                        element={data}
                        key={index}
                        selected={img}
                        selectImage={selectImage}
                      />
                    )
                  )
                : [...Array(limit)].map((elem, idx) => (
                    <Skeleton
                      height={150}
                      width={150}
                      radius="sm"
                      key={idx}
                      style={{ padding: '5px' }}
                    />
                  ))}
            </SimpleGrid>
          </>
        </Paper>
      </Suspense>

      <Divider />
      <Paper p="sm">
        <Group position="apart">
          <TextInput
            placeholder={t`Search...`}
            onChange={(event) => {
              setFilterInput(event.currentTarget.value);
            }}
          />
          <Button
            disabled={!img}
            onClick={() => setNewImage(img, pk, close, setImage)}
          >
            <Trans>Select</Trans>
          </Button>
        </Group>
      </Paper>
    </>
  );
}
