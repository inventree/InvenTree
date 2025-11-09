import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  AspectRatio,
  Button,
  Divider,
  Group,
  Pagination,
  Paper,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useDebouncedValue, useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';
import type React from 'react';
import { Suspense, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { ModelType } from '@lib/index';
import { IconX } from '@tabler/icons-react';
import { api } from '../../App';
import { Thumbnail } from '../../components/images/Thumbnail';
import { showApiErrorMessage } from '../../functions/notifications';

/**
 * Input props to table
 */
export type ThumbTableProps = {
  pk: string;
  onSuccess: (image: string) => void;
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
function PartThumbComponent({
  selected,
  element,
  selectImage
}: Readonly<ThumbProps>) {
  const { hovered, ref } = useHover();

  const hoverColor = 'rgba(127,127,127,0.2)';
  const selectedColor = 'rgba(127,127,127,0.29)';

  let color = '';

  if (selected === element.image) {
    color = selectedColor;
  } else if (hovered) {
    color = hoverColor;
  }

  const src: string | undefined = element?.image ? element?.image : undefined;

  return (
    <Paper
      withBorder
      style={{ backgroundColor: color }}
      p='sm'
      ref={ref}
      onClick={() => selectImage(element.image)}
    >
      <Stack justify='space-between'>
        <AspectRatio ratio={1}>
          <Thumbnail size={120} src={src} align='center' />
        </AspectRatio>
        <Text size='xs'>
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
  onSuccess: (image: string) => void,
  image: string | null,
  object_id: string
) {
  // No need to do anything if no image is selected
  if (image === null) {
    return;
  }

  await api
    .post(apiUrl(ApiEndpoints.upload_image_list), {
      existing_image: image,
      content_type: ModelType.part,
      object_id: object_id
    })
    .then((response) => {
      // Update the image in the parent component
      modals.closeAll();
      onSuccess(response.data.image);
      return response;
    })
    .catch((error) => {
      // Handle error
      showApiErrorMessage({
        error: error,
        title: t`Set Image Error`,
        field: 'image'
      });
      modals.closeAll();
      return error.response;
    });
}

/**
 * Renders a "table" of thumbnails
 */
export function PartThumbTable({ pk, onSuccess }: Readonly<ThumbTableProps>) {
  const limit = 24;

  const [thumbImage, setThumbImage] = useState<string | null>(null);
  const [filterInput, setFilterInput] = useState<string>('');

  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  // Keep search filters from updating while user is typing
  const [searchText] = useDebouncedValue(filterInput, 500);

  // Fetch thumbnails from API
  const thumbQuery = useQuery({
    queryKey: [ApiEndpoints.part_thumbs_list, page, searchText],
    throwOnError: (error: any) => {
      setTotalPages(1);
      setPage(1);
      return true;
    },
    queryFn: async () => {
      const offset = Math.max(0, page - 1) * limit;

      return api
        .get(apiUrl(ApiEndpoints.upload_image_thumbs_list), {
          params: {
            offset: offset,
            limit: limit,
            search: searchText,
            content_model: ModelType.part
          }
        })
        .then((response) => {
          const records = response?.data?.count ?? 1;
          setTotalPages(Math.ceil(records / limit));
          return response.data?.results ?? response.data;
        });
    }
  });

  return (
    <>
      <Suspense>
        <Divider />
        <Paper p='sm'>
          <SimpleGrid
            cols={{ base: 2, '450px': 3, '600px': 4, '900px': 6 }}
            type='container'
            spacing='xs'
          >
            {!thumbQuery.isFetching
              ? thumbQuery?.data?.map((data: ImageElement, index: number) => (
                  <PartThumbComponent
                    element={data}
                    key={index}
                    selected={thumbImage}
                    selectImage={setThumbImage}
                  />
                ))
              : [...Array(limit)].map((elem, idx) => (
                  <Skeleton
                    height={150}
                    width={150}
                    radius='sm'
                    key={idx}
                    style={{ padding: '5px' }}
                  />
                ))}
          </SimpleGrid>
        </Paper>
      </Suspense>

      <Divider />
      <Paper p='sm'>
        <Group justify='space-between' gap='xs'>
          <Group justify='left' gap='xs'>
            <TextInput
              placeholder={t`Search...`}
              value={filterInput}
              onChange={(event) => {
                setFilterInput(event.currentTarget.value);
              }}
              rightSection={
                <IconX
                  size='1rem'
                  color='red'
                  onClick={() => setFilterInput('')}
                />
              }
            />
            <Pagination
              total={totalPages}
              value={page}
              onChange={(value) => setPage(value)}
            />
          </Group>
          <Button
            disabled={!thumbImage}
            onClick={() => setNewImage(onSuccess, thumbImage, pk)}
          >
            <Trans>Select</Trans>
          </Button>
        </Group>
      </Paper>
    </>
  );
}
