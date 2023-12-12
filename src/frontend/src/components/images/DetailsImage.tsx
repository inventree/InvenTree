import { Group, Paper, Text } from '@mantine/core';
import { useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { IconFileUpload, IconGridDots, IconTrash } from '@tabler/icons-react';

import { api } from '../../App';
import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from './ApiImage';

export type DetailImageProps = {
  src: string;
  apiPath: string;
  refresh: any;
  imageActions?: DetailImageButtonProps;
};

export type DetailImageButtonProps = {
  selectExisting?: boolean;
  uploadFile?: boolean;
  deleteFile?: boolean;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

// Image to display if instance has no image
const backup_image = '/static/img/blank_image.png';

const removeModal = (apiPath: string, refresh: any) =>
  modals.openConfirmModal({
    title: 'Remove Image',
    children: (
      <Text size="sm">Remove the associated image from this part?</Text>
    ),
    labels: { confirm: 'Remove', cancel: 'Cancel' },
    onConfirm: async () => {
      await api.patch(apiPath, { image: null });
      refresh();
    }
  });

// TODO: Docstrings
function ImageActionButtons({
  actions = {},
  visible,
  apiPath,
  hasImage,
  refresh
}: {
  actions?: DetailImageButtonProps;
  visible: boolean;
  apiPath: string;
  hasImage: boolean;
  refresh: any;
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
            tooltipAlignment="top"
          />
        )}
        {actions.uploadFile && (
          <ActionButton
            icon={<IconFileUpload />}
            tooltip="Upload new image"
            variant="outline"
            size="lg"
            tooltipAlignment="top"
          />
        )}
        {actions.deleteFile && hasImage && (
          <ActionButton
            icon={<IconTrash color="red" />}
            tooltip="Delete image"
            variant="outline"
            size="lg"
            tooltipAlignment="top"
            onClick={() => removeModal(apiPath, refresh)}
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
        src={props.src ?? backup_image}
        style={{ zIndex: 1 }}
        height={IMAGE_DIMENSION}
        width={IMAGE_DIMENSION}
      />
      <ImageActionButtons
        visible={hovered}
        actions={props.imageActions}
        apiPath={props.apiPath}
        hasImage={props.src ? true : false}
        refresh={props.refresh}
      />
    </Paper>
  );
}
