import { Trans, t } from '@lingui/macro';
import {
  AspectRatio,
  Button,
  Grid,
  Group,
  Image,
  Overlay,
  Paper,
  Text,
  rem,
  useMantineColorScheme
} from '@mantine/core';
import {
  Dropzone,
  type FileWithPath,
  IMAGE_MIME_TYPE
} from '@mantine/dropzone';
import { useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useMemo, useState } from 'react';

import { showNotification } from '@mantine/notifications';
import { api } from '../../App';
import type { UserRoles } from '../../enums/Roles';
import { cancelEvent } from '../../functions/events';
import { InvenTreeIcon } from '../../functions/icons';
import { showApiErrorMessage } from '../../functions/notifications';
import { useEditApiFormModal } from '../../hooks/UseForm';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { PartThumbTable } from '../../tables/part/PartThumbTable';
import { vars } from '../../theme';
import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from '../images/ApiImage';
import { StylishText } from '../items/StylishText';

/**
 * Props for detail image
 */
export type DetailImageProps = {
  appRole: UserRoles;
  src: string;
  apiPath: string;
  refresh?: () => void;
  imageActions?: DetailImageButtonProps;
  pk: string;
};

/**
 * Actions for Detail Images.
 * If true, the button type will be visible
 * @param {boolean} selectExisting - PART ONLY. Allows selecting existing images as part image
 * @param {boolean} downloadImage - Allows downloading image from a remote URL
 * @param {boolean} uploadFile - Allows uploading a new image
 * @param {boolean} deleteFile - Allows deleting the current image
 */
export type DetailImageButtonProps = {
  selectExisting?: boolean;
  downloadImage?: boolean;
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
    title: <StylishText size='xl'>{t`Remove Image`}</StylishText>,
    children: (
      <Text>
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
}: Readonly<{
  apiPath: string;
  setImage: (image: string) => void;
}>) {
  const [currentFile, setCurrentFile] = useState<FileWithPath | null>(null);
  let uploading = false;

  // Components to show in the Dropzone when no file is selected
  const noFileIdle = (
    <Group>
      <InvenTreeIcon icon='photo' iconProps={{ size: '3.2rem', stroke: 1.5 }} />
      <div>
        <Text size='xl' inline>
          <Trans>Drag and drop to upload</Trans>
        </Text>
        <Text size='sm' c='dimmed' inline mt={7}>
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
          onLoad={() => URL.revokeObjectURL(imageUrl)}
          radius='sm'
          height={75}
          fit='contain'
          style={{ flexBasis: '40%' }}
        />
        <div style={{ flexBasis: '60%' }}>
          <Text size='xl' inline style={{ wordBreak: 'break-all' }}>
            {file.name}
          </Text>
          <Text size='sm' c='dimmed' inline mt={7}>
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

    api
      .patch(apiPath, formData)
      .then((response) => {
        setImage(response.data.image);
        modals.closeAll();
        showNotification({
          title: t`Image uploaded`,
          message: t`Image has been uploaded successfully`,
          color: 'green'
        });
      })
      .catch((error) => {
        showApiErrorMessage({
          error: error,
          title: t`Upload Error`,
          field: 'image'
        });
      });
  };

  const { colorScheme } = useMantineColorScheme();

  const primaryColor =
    vars.colors.primaryColors[colorScheme === 'dark' ? 4 : 6];
  const redColor = vars.colors.red[colorScheme === 'dark' ? 4 : 6];

  return (
    <Paper style={{ height: '220px' }}>
      <Dropzone
        onDrop={(files) => setCurrentFile(files[0])}
        maxFiles={1}
        accept={IMAGE_MIME_TYPE}
        loading={uploading}
      >
        <Group
          justify='center'
          gap='xl'
          style={{ minHeight: rem(140), pointerEvents: 'none' }}
        >
          <Dropzone.Accept>
            <InvenTreeIcon
              icon='upload'
              iconProps={{
                size: '3.2rem',
                stroke: 1.5,
                color: primaryColor
              }}
            />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <InvenTreeIcon
              icon='reject'
              iconProps={{
                size: '3.2rem',
                stroke: 1.5,
                color: redColor
              }}
            />
          </Dropzone.Reject>
          <Dropzone.Idle>
            {currentFile ? fileInfo(currentFile) : noFileIdle}
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
          variant='outline'
          disabled={!currentFile}
          onClick={() => setCurrentFile(null)}
        >
          <Trans>Clear</Trans>
        </Button>
        <Button
          disabled={!currentFile}
          onClick={() => uploadImage(currentFile)}
        >
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
  setImage,
  downloadImage
}: Readonly<{
  actions?: DetailImageButtonProps;
  visible: boolean;
  apiPath: string;
  hasImage: boolean;
  pk: string;
  setImage: (image: string) => void;
  downloadImage: () => void;
}>) {
  const globalSettings = useGlobalSettingsState();

  return (
    <>
      {visible && (
        <Group
          gap='xs'
          style={{ zIndex: 2, position: 'absolute', top: '10px', left: '10px' }}
        >
          {actions.selectExisting && (
            <ActionButton
              icon={
                <InvenTreeIcon
                  icon='select_image'
                  iconProps={{ color: 'white' }}
                />
              }
              tooltip={t`Select from existing images`}
              variant='outline'
              size='lg'
              tooltipAlignment='top'
              onClick={(event: any) => {
                cancelEvent(event);

                modals.open({
                  title: <StylishText size='xl'>{t`Select Image`}</StylishText>,
                  size: '80%',
                  children: <PartThumbTable pk={pk} setImage={setImage} />
                });
              }}
            />
          )}
          {actions.downloadImage &&
            globalSettings.isSet('INVENTREE_DOWNLOAD_FROM_URL') && (
              <ActionButton
                icon={
                  <InvenTreeIcon
                    icon='download'
                    iconProps={{ color: 'white' }}
                  />
                }
                tooltip={t`Download remote image`}
                variant='outline'
                size='lg'
                tooltipAlignment='top'
                onClick={(event: any) => {
                  cancelEvent(event);
                  downloadImage();
                }}
              />
            )}
          {actions.uploadFile && (
            <ActionButton
              icon={
                <InvenTreeIcon icon='upload' iconProps={{ color: 'white' }} />
              }
              tooltip={t`Upload new image`}
              variant='outline'
              size='lg'
              tooltipAlignment='top'
              onClick={(event: any) => {
                cancelEvent(event);
                modals.open({
                  title: <StylishText size='xl'>{t`Upload Image`}</StylishText>,
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
                <InvenTreeIcon icon='delete' iconProps={{ color: 'red' }} />
              }
              tooltip={t`Delete image`}
              variant='outline'
              size='lg'
              tooltipAlignment='top'
              onClick={(event: any) => {
                cancelEvent(event);
                removeModal(apiPath, setImage);
              }}
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
export function DetailsImage(props: Readonly<DetailImageProps>) {
  // Displays a group of ActionButtons on hover
  const { hovered, ref } = useHover();
  const [img, setImg] = useState<string>(props.src ?? backup_image);

  // Sets a new image, and triggers upstream instance refresh
  const setAndRefresh = (image: string) => {
    setImg(image);
    props.refresh?.();
  };

  const permissions = useUserState();

  const downloadImage = useEditApiFormModal({
    url: props.apiPath,
    title: t`Download Image`,
    fields: {
      remote_image: {}
    },
    timeout: 10000,
    successMessage: t`Image downloaded successfully`,
    onFormSuccess: (response: any) => {
      if (response.image) {
        setAndRefresh(response.image);
      }
    }
  });

  const hasOverlay: boolean = useMemo(() => {
    return (
      props.imageActions?.selectExisting ||
      props.imageActions?.uploadFile ||
      props.imageActions?.deleteFile ||
      false
    );
  }, [props.imageActions]);

  const expandImage = (event: any) => {
    cancelEvent(event);
    modals.open({
      children: <ApiImage src={img} />,
      withCloseButton: false
    });
  };

  return (
    <>
      {downloadImage.modal}
      <Grid.Col span={{ base: 12, sm: 4 }}>
        <AspectRatio
          ref={ref}
          maw={IMAGE_DIMENSION}
          ratio={1}
          pos='relative'
          visibleFrom='xs'
        >
          <>
            <ApiImage
              src={img}
              mah={IMAGE_DIMENSION}
              maw={IMAGE_DIMENSION}
              onClick={expandImage}
            />
            {permissions.hasChangeRole(props.appRole) &&
              hasOverlay &&
              hovered && (
                <Overlay color='black' opacity={0.8} onClick={expandImage}>
                  <ImageActionButtons
                    visible={hovered}
                    actions={props.imageActions}
                    apiPath={props.apiPath}
                    hasImage={!!props.src}
                    pk={props.pk}
                    setImage={setAndRefresh}
                    downloadImage={downloadImage.open}
                  />
                </Overlay>
              )}
          </>
        </AspectRatio>
      </Grid.Col>
    </>
  );
}
