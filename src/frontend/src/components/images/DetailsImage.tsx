import { Trans, t } from '@lingui/macro';
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
import { ModalSettings } from '@mantine/modals/lib/context';
import { useState } from 'react';

import { api } from '../../App';
import { UserRoles } from '../../enums/Roles';
import { InvenTreeIcon } from '../../functions/icons';
import { useUserState } from '../../states/UserState';
import { ActionButton } from '../buttons/ActionButton';
import { PartThumbTable } from '../tables/part/PartThumbTable';
import { ApiImage } from './ApiImage';

/**
 * Props for detail image
 */
export type DetailImageProps = {
  appRole: UserRoles;
  src: string;
  apiPath: string;
  refresh: () => void;
  imageActions?: DetailImageButtonProps;
  pk: string;
};

/**
 * Actions for Detail Images.
 * If true, the button type will be visible
 * @param {boolean} selectExisting - PART ONLY. Allows selecting existing images as part image
 * @param {boolean} uploadFile - Allows uploading a new image
 * @param {boolean} deleteFile - Allows deleting the current image
 */
export type DetailImageButtonProps = {
  selectExisting?: boolean;
  uploadFile?: boolean;
  deleteFile?: boolean;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

// Image to display if instance has no image
const backup_image = '/static/img/blank_image.png';

/**
 * Modal used for removing/deleting the current image relation
 */
const removeModal = (apiPath: string, setImage: (image: string) => void) =>
  modals.openConfirmModal({
    title: t`Remove Image`,
    children: (
      <Text size="sm">
        <Trans>Remove the associated image from this item?</Trans>
      </Text>
    ),
    labels: { confirm: t`Remove`, cancel: t`Cancel` },
    onConfirm: async () => {
      await api.patch(apiPath, { image: null });
      setImage(backup_image);
    }
  });

/**
 * Modal used for uploading a new image
 */
function UploadModal({
  apiPath,
  setImage
}: {
  apiPath: string;
  setImage: (image: string) => void;
}) {
  const [file1, setFile] = useState<FileWithPath | null>(null);
  let uploading = false;

  const theme = useMantineTheme();

  // Components to show in the Dropzone when no file is selected
  const noFileIdle = (
    <Group>
      <InvenTreeIcon icon="photo" iconProps={{ size: '3.2rem', stroke: 1.5 }} />
      <div>
        <Text size="xl" inline>
          <Trans>Drag and drop to upload</Trans>
        </Text>
        <Text size="sm" color="dimmed" inline mt={7}>
          <Trans>Click to select file(s)</Trans>
        </Text>
      </div>
    </Group>
  );

  /**
   * Generates components to display selected image in Dropzone
   */
  const fileInfo = (file: FileWithPath) => {
    const imageUrl = URL.createObjectURL(file);
    const size = file.size / 1024 ** 2;

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

  /**
   * Create FormData object and upload selected image
   */
  const uploadImage = async (file: FileWithPath | null) => {
    if (!file) {
      return;
    }

    uploading = true;
    const formData = new FormData();
    formData.append('image', file, file.name);

    const response = await api.patch(apiPath, formData);

    if (response.data.image.includes(file.name)) {
      setImage(response.data.image);
      modals.closeAll();
    }
  };

  const primaryColor =
    theme.colors[theme.primaryColor][theme.colorScheme === 'dark' ? 4 : 6];
  const redColor = theme.colors.red[theme.colorScheme === 'dark' ? 4 : 6];

  return (
    <Paper sx={{ height: '220px' }}>
      <Dropzone
        onDrop={(files) => setFile(files[0])}
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
            <InvenTreeIcon
              icon="upload"
              iconProps={{
                size: '3.2rem',
                stroke: 1.5,
                color: primaryColor
              }}
            />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <InvenTreeIcon
              icon="reject"
              iconProps={{
                size: '3.2rem',
                stroke: 1.5,
                color: redColor
              }}
            />
          </Dropzone.Reject>
          <Dropzone.Idle>{file1 ? fileInfo(file1) : noFileIdle}</Dropzone.Idle>
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
          <Trans>Clear</Trans>
        </Button>
        <Button disabled={!file1} onClick={() => uploadImage(file1)}>
          <Trans>Submit</Trans>
        </Button>
      </Paper>
    </Paper>
  );
}

/**
 * Generate components for Action buttons used with the Details Image
 */
function ImageActionButtons({
  actions = {},
  visible,
  apiPath,
  hasImage,
  pk,
  setImage
}: {
  actions?: DetailImageButtonProps;
  visible: boolean;
  apiPath: string;
  hasImage: boolean;
  pk: string;
  setImage: (image: string) => void;
}) {
  const [opened, { open, close }] = useDisclosure(false);

  return (
    <>
      <Modal opened={opened} onClose={close} title={t`Select image`} size="70%">
        <PartThumbTable pk={pk} close={close} setImage={setImage} />
      </Modal>
      {visible && (
        <Group
          spacing="xs"
          style={{ zIndex: 2, position: 'absolute', top: '10px', left: '10px' }}
        >
          {actions.selectExisting && (
            <ActionButton
              icon={<InvenTreeIcon icon="select_image" />}
              tooltip={t`Select from existing images`}
              variant="outline"
              size="lg"
              tooltipAlignment="top"
              onClick={open}
            />
          )}
          {actions.uploadFile && (
            <ActionButton
              icon={<InvenTreeIcon icon="upload" />}
              tooltip={t`Upload new image`}
              variant="outline"
              size="lg"
              tooltipAlignment="top"
              onClick={() => {
                modals.open({
                  title: t`Upload Image`,
                  children: (
                    <UploadModal apiPath={apiPath} setImage={setImage} />
                  )
                });
              }}
            />
          )}
          {actions.deleteFile && hasImage && (
            <ActionButton
              icon={
                <InvenTreeIcon icon="delete" iconProps={{ color: 'red' }} />
              }
              tooltip={t`Delete image`}
              variant="outline"
              size="lg"
              tooltipAlignment="top"
              onClick={() => removeModal(apiPath, setImage)}
            />
          )}
        </Group>
      )}
    </>
  );
}

/**
 * Renders an image with action buttons for display on Details panels
 */
export function DetailsImage(props: DetailImageProps) {
  // Displays a group of ActionButtons on hover
  const { hovered, ref } = useHover();
  const [img, setImg] = useState<string>(props.src ?? backup_image);

  // Sets a new image, and triggers upstream instance refresh
  const setAndRefresh = (image: string) => {
    setImg(image);
    props.refresh();
  };

  const permissions = useUserState();

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
          onClick={() => {
            modals.open({
              children: <ApiImage src={img} />,
              withCloseButton: false
            });
          }}
        />
        {permissions.hasChangeRole(props.appRole) && (
          <ImageActionButtons
            visible={hovered}
            actions={props.imageActions}
            apiPath={props.apiPath}
            hasImage={props.src ? true : false}
            pk={props.pk}
            setImage={setAndRefresh}
          />
        )}
      </Paper>
    </>
  );
}
