import { Button, Paper, Skeleton, Text, TextInput } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { Suspense, useEffect, useState } from 'react';

import { api } from '../../../App';
import { ApiPaths } from '../../../enums/ApiEndpoints';
import { apiUrl } from '../../../states/ApiState';
import { Thumbnail } from '../../images/Thumbnail';

export type ThumbTableProps = {
  pk: string;
  limit?: number;
  offset?: number;
  search?: string;
  close: any;
  setImage: any;
};

type ThumbProps = {
  selected: string | null;
  element: any;
  setImage: any;
};

/*
 * Renders a single image thumbnail
 */
function PartThumbComponent({ selected, element, setImage }: ThumbProps) {
  const { hovered, ref } = useHover();

  const hoverColor = 'rgba(127,127,127,0.2)';
  const selectedColor = 'rgba(127,127,127,0.29)';

  let color = '';

  if (selected === element?.image) {
    color = selectedColor;
  } else if (hovered) {
    color = hoverColor;
  }

  const src = element?.image ? `/media/${element?.image}` : undefined;

  return (
    <Paper
      withBorder
      style={{
        backgroundColor: color,
        padding: '5px',
        display: 'flex',
        flex: '0 1 150px',
        flexFlow: 'column wrap',
        placeContent: 'center space-between'
      }}
      ref={ref}
      onClick={() => setImage(element.image)}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          flexGrow: 1
        }}
      >
        <Thumbnail size={120} src={src} align="center"></Thumbnail>
      </div>
      <Text style={{ alignSelf: 'center', overflowWrap: 'anywhere' }}>
        {element.image.split('/')[1]} ({element.count})
      </Text>
    </Paper>
  );
}

/*
 * Changes a part's image to the supplied URL and updates the DOM accordingly
 */
async function setNewImage(
  image: string | null,
  pk: string,
  close: any,
  setImage: any
) {
  // No need to do anything if no image is selected
  if (image === null) {
    return;
  }

  const response = await api.patch(apiUrl(ApiPaths.part_list, pk), {
    existing_image: image
  });

  // Update image component and close modal if update was successful
  if (response.data.image.includes(image)) {
    setImage(response.data.image);
    close();
  }
}

/*
 * Renders a "table" of thumbnails
 */
export function PartThumbTable({
  limit = 25,
  offset = 0,
  search = '',
  pk,
  close,
  setImage
}: ThumbTableProps) {
  const [img, setImg] = useState(null);
  const [filterInput, setFilterInput] = useState('');
  const [filterQuery, setFilter] = useState(search);

  // Keep search filters from updating while user is typing
  useEffect(() => {
    const timeoutId = setTimeout(() => setFilter(filterInput), 500);
    return () => clearTimeout(timeoutId);
  }, [filterInput]);

  // Fetch thumbnails from API
  const thumbQuery = useQuery({
    queryKey: [
      apiUrl(ApiPaths.part_thumbs_list),
      { limit: limit, offset: offset, search: filterQuery }
    ],
    queryFn: async () => {
      return api.get(apiUrl(ApiPaths.part_thumbs_list), {
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
        <Paper
          style={{
            display: 'flex',
            alignItems: 'stretch',
            placeContent: 'stretch center',
            flexWrap: 'wrap',
            gap: '10px'
          }}
        >
          {!thumbQuery.isFetching
            ? thumbQuery.data?.data.map((data: any, index: number) => (
                <PartThumbComponent
                  element={data}
                  key={index}
                  selected={img}
                  setImage={setImg}
                />
              ))
            : [...Array(limit)].map((elem, idx) => (
                <Skeleton
                  height={150}
                  width={150}
                  radius="sm"
                  key={idx}
                  style={{ padding: '5px' }}
                />
              ))}
        </Paper>
      </Suspense>
      <Paper
        style={{
          position: 'sticky',
          bottom: 0,
          left: 0,
          right: 0,
          height: '60px',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          flexDirection: 'row',
          justifyContent: 'space-between'
        }}
      >
        <TextInput
          placeholder="Search..."
          onChange={(event) => {
            setFilterInput(event.currentTarget.value);
          }}
        />
        <Button
          disabled={!img}
          onClick={() => setNewImage(img, pk, close, setImage)}
        >
          Submit
        </Button>
      </Paper>
    </>
  );
}
