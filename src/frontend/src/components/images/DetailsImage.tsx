import { Group, Paper } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { IconFileUpload, IconGridDots, IconTrash } from '@tabler/icons-react';

import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from './ApiImage';

export type DetailImageProps = {
  src: string;
  imageActions?: DetailImageButtonProps;
};

export type DetailImageButtonProps = {
  selectExisting?: boolean;
  uploadFile?: boolean;
  deleteFile?: boolean;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

// TODO: Docstrings
function ImageActionButtons({
  actions = {},
  visible
}: {
  actions?: DetailImageButtonProps;
  visible: boolean;
}) {
  return (
    visible && (
      <Group
        spacing="xs"
        style={{ zIndex: 2, position: 'absolute', top: '10px', left: '10px' }}
      >
        {actions.selectExisting && (
          <ActionButton
            icon={<IconGridDots />}
            tooltip="Select from existing images"
            variant="outline"
            size="lg"
          />
        )}
        {actions.uploadFile && (
          <ActionButton
            icon={<IconFileUpload />}
            tooltip="Upload new image"
            variant="outline"
            size="lg"
          />
        )}
        {actions.deleteFile && (
          <ActionButton
            icon={<IconTrash />}
            tooltip="Delete image"
            variant="outline"
            size="lg"
          />
        )}
      </Group>
    )
  );
}

// TODO: Docstrings
export function DetailsImage(props: DetailImageProps) {
  // Displays a group of ActionButtons on hover
  const { hovered, ref } = useHover();

  return (
    <Paper
      ref={ref}
      style={{
        position: 'relative',
        width: `${IMAGE_DIMENSION}px`,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}
    >
      <ApiImage
        src={props.src}
        style={{ zIndex: 1 }}
        height={IMAGE_DIMENSION}
        width={IMAGE_DIMENSION}
      />
      <ImageActionButtons visible={hovered} actions={props.imageActions} />
    </Paper>
  );
}
