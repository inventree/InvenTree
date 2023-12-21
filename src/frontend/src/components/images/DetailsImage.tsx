import { Group, Modal, Paper, Text } from '@mantine/core';
import { useDisclosure, useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { IconFileUpload, IconGridDots, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { api } from '../../App';
import { ActionButton } from '../buttons/ActionButton';
import { PartThumbTable } from '../tables/part/PartThumbTable';
import { ApiImage } from './ApiImage';

export type DetailImageProps = {
  src: string;
  apiPath: string;
  refresh: any;
  imageActions?: DetailImageButtonProps;
  pk: string;
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
  refresh,
  pk,
  setImage
}: {
  actions?: DetailImageButtonProps;
  visible: boolean;
  apiPath: string;
  hasImage: boolean;
  refresh: any;
  pk: string;
  setImage: any;
}) {
  const [opened, { open, close }] = useDisclosure(false);

  return (
    <>
      <Modal opened={opened} onClose={close} title="Select image" size="70%">
        <PartThumbTable pk={pk} close={close} setImage={setImage} />
      </Modal>
      {visible && (
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
              onClick={open}
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
      )}
    </>
  );
}

// TODO: Docstrings
export function DetailsImage(props: DetailImageProps) {
  // Displays a group of ActionButtons on hover
  const { hovered, ref } = useHover();
  const [img, setImg] = useState(props.src ?? backup_image);

  return (
    <>
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
          src={img}
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
          pk={props.pk}
          setImage={setImg}
        />
      </Paper>
    </>
  );
}
