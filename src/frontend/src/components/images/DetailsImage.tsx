import { ActionIcon, Group, Menu, Paper, Tooltip } from '@mantine/core';
import { IconFileUpload, IconGridDots, IconTrash } from '@tabler/icons-react';

import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from './ApiImage';

export type DetailImageProps = {
  src: string;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

const actions = {};

function ImageActionButtons({ props = {} }: { props?: any }) {
  return (
    <Group {...props} spacing="xs" style={{ zIndex: 2 }}>
      <Paper withBorder radius="sm">
        <ActionButton
          icon={<IconGridDots />}
          tooltip="Select from existing images"
        />
      </Paper>
      <Paper withBorder radius="sm">
        <ActionButton icon={<IconFileUpload />} tooltip="Upload new image" />
      </Paper>
      <Paper withBorder radius="sm">
        <ActionButton icon={<IconTrash />} tooltip="Delete image" />
      </Paper>
    </Group>
  );
}

export function DetailsImage(props: DetailImageProps) {
  return (
    <Paper>
      <ApiImage
        {...props}
        style={{ zIndex: 1 }}
        height={IMAGE_DIMENSION}
        width={IMAGE_DIMENSION}
      />
      <ImageActionButtons />
    </Paper>
  );
}
