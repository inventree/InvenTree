import {
  Button,
  Group,
  Image,
  Modal,
  Paper,
  Text,
  rem,
  useMantineTheme
} from '@mantine/core';
import { Dropzone, FileWithPath, IMAGE_MIME_TYPE } from '@mantine/dropzone';
import { useDisclosure, useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import {
  IconFileUpload,
  IconGridDots,
  IconPhoto,
  IconTrash,
  IconUpload,
  IconX
} from '@tabler/icons-react';
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

const removeModal = (apiPath: string, refresh: any, setImage: any) =>
  modals.openConfirmModal({
    title: 'Remove Image',
    children: (
      <Text size="sm">Remove the associated image from this part?</Text>
    ),
    labels: { confirm: 'Remove', cancel: 'Cancel' },
    onConfirm: async () => {
      await api.patch(apiPath, { image: null });
      refresh();
      setImage(backup_image);
    }
  });

function UploadModal({
  apiPath,
  refresh,
  setImage
}: {
  apiPath: string;
  refresh: any;
  setImage: any;
}) {
  const [file1, setFile] = useState<FileWithPath | null>(null);
  let uploading = false;

  const theme = useMantineTheme();

  const noFileIdle = (
    <Group>
      <IconPhoto size="3.2rem" stroke={1.5} />
      <div>
        <Text size="xl" inline>
          Drag and drop to upload
        </Text>
        <Text size="sm" color="dimmed" inline mt={7}>
          Click to select file(s)
        </Text>
      </div>
    </Group>
  );

  const fileInfo = (file: FileWithPath) => {
    const imageUrl = URL.createObjectURL(file);
    const size = file.size / 1024 ** 2;
    console.log(file);
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '15px',
          flexGrow: '1'
        }}
      >
        <Image
          src={imageUrl}
          imageProps={{ onLoad: () => URL.revokeObjectURL(imageUrl) }}
          radius="sm"
          height={75}
          fit="contain"
          style={{ flexBasis: '40%' }}
        />
        <div style={{ flexBasis: '60%' }}>
          <Text size="xl" inline style={{ wordBreak: 'break-all' }}>
            {file.name}
          </Text>
          <Text size="sm" color="dimmed" inline mt={7}>
            {size.toFixed(2)} MB
          </Text>
        </div>
      </div>
    );
  };

  const uploadImage = async (file: FileWithPath | null) => {
    if (!file) {
      return;
    }

    uploading = true;

    const formData = new FormData();

    formData.append('image', file, file.name);

    const response = await api.patch(apiPath, formData);

    if (response.data.image.includes(file.name)) {
      refresh();
      setImage(response.data.image);
      modals.closeAll();
    }
  };

  return (
    <Paper sx={{ height: '220px' }}>
      <form>
        <Dropzone
          onDrop={(file) => setFile(file[0])}
          onReject={(files) => console.log('rejected files', files)}
          maxFiles={1}
          accept={IMAGE_MIME_TYPE}
          loading={uploading}
        >
          <Group
            position="center"
            spacing="xl"
            style={{ minHeight: rem(140), pointerEvents: 'none' }}
          >
            <Dropzone.Accept>
              <IconUpload
                size="3.2rem"
                stroke={1.5}
                color={
                  theme.colors[theme.primaryColor][
                    theme.colorScheme === 'dark' ? 4 : 6
                  ]
                }
              />
            </Dropzone.Accept>
            <Dropzone.Reject>
              <IconX
                size="3.2rem"
                stroke={1.5}
                color={theme.colors.red[theme.colorScheme === 'dark' ? 4 : 6]}
              />
            </Dropzone.Reject>
            <Dropzone.Idle>
              {file1 ? fileInfo(file1) : noFileIdle}
            </Dropzone.Idle>
          </Group>
        </Dropzone>
        <Paper
          style={{
            position: 'sticky',
            bottom: '0',
            left: '0',
            right: '0',
            height: '60px',
            zIndex: 1,
            display: 'flex',
            alignItems: 'center',
            flexDirection: 'row',
            justifyContent: 'flex-end',
            gap: '10px'
          }}
        >
          <Button
            variant="outline"
            disabled={!file1}
            onClick={() => setFile(null)}
          >
            Clear
          </Button>
          <Button disabled={!file1} onClick={() => uploadImage(file1)}>
            Submit
          </Button>
        </Paper>
      </form>
    </Paper>
  );
}

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
              onClick={() => {
                modals.open({
                  title: 'Upload Image',
                  children: (
                    <UploadModal
                      apiPath={apiPath}
                      refresh={refresh}
                      setImage={setImage}
                    />
                  )
                });
              }}
            />
          )}
          {actions.deleteFile && hasImage && (
            <ActionButton
              icon={<IconTrash color="red" />}
              tooltip="Delete image"
              variant="outline"
              size="lg"
              tooltipAlignment="top"
              onClick={() => removeModal(apiPath, refresh, setImage)}
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
