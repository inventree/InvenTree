import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  AspectRatio,
  Button,
  Checkbox,
  Flex,
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

import type { UserRoles } from '@lib/enums/Roles';
import { cancelEvent } from '@lib/functions/Events';
import { ApiEndpoints, ModelType, apiUrl } from '@lib/index';
import { Carousel } from '@mantine/carousel';
import { showNotification } from '@mantine/notifications';
import { IconCameraPlus, IconDotsVertical } from '@tabler/icons-react';
import { api } from '../../App';
import { InvenTreeIcon } from '../../functions/icons';
import { showApiErrorMessage } from '../../functions/notifications';
import {
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { PartThumbTable } from '../../tables/part/PartThumbTable';
import { vars } from '../../theme';
import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from '../images/ApiImage';
import {
  ActionDropdown,
  type ActionDropdownItem
} from '../items/ActionDropdown';
import { StylishText } from '../items/StylishText';

/**
 * Props for detail image
 */
export type DetailImageProps = {
  appRole?: UserRoles;
  primary?: boolean;
  src: string;
  apiPath: string;
  refresh?: () => void;
  imageActions?: DetailImageButtonProps;
  pk: string;
  model_id?: string;
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
  setImage,
  model_id
}: Readonly<{
  setImage: (image: string) => void;
  model_id: string;
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
    formData.append('model_type', ModelType.part);
    formData.append('model_id', model_id);

    const url = apiUrl(ApiEndpoints.upload_image_list);

    api
      .post(url, formData)
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

      <Checkbox defaultChecked label='Set as primary' />

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
  downloadImage,
  deleteUploadImage
}: Readonly<{
  actions?: DetailImageButtonProps;
  visible: boolean;
  apiPath: string;
  hasImage: boolean;
  pk: string;
  setImage: (image: string) => void;
  downloadImage: () => void;
  deleteUploadImage: () => void;
}>) {
  const globalSettings = useGlobalSettingsState();

  // const url = apiUrl(ApiEndpoints.upload_image_list);

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
                  children: <UploadModal model_id={pk} setImage={setImage} />
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
                deleteUploadImage();
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

  // Modal used for removing/deleting the current image
  const deleteUploadImage = useDeleteApiFormModal({
    url: ApiEndpoints.upload_image_list,
    pk: props.pk,
    title: t`Delete Image`,
    onFormSuccess: () => {
      props.refresh?.();
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

  const imageActions: ActionDropdownItem[] = [
    {
      name: 'Set as primary',
      onClick: (event: any) => {
        cancelEvent(event);
      },
      icon: <InvenTreeIcon icon='complete' />
    },
    {
      name: 'Delete image',
      onClick: (event: any) => {
        cancelEvent(event);
        deleteUploadImage.open();
      },
      icon: <InvenTreeIcon icon='delete' iconProps={{ color: 'red' }} />
    }
  ];

  const newImageActions: ActionDropdownItem[] = [
    {
      name: 'Upload new image',
      onClick: (event: any) => {
        cancelEvent(event);
        modals.open({
          title: <StylishText size='xl'>{t`Upload Image`}</StylishText>,
          children: (
            <UploadModal model_id={props.model_id!} setImage={setAndRefresh} />
          )
        });
      },
      icon: <InvenTreeIcon icon='upload' />
    },
    {
      name: 'Select from existing images',
      onClick: (event: any) => {
        cancelEvent(event);
        modals.open({
          title: <StylishText size='xl'>{t`Select Image`}</StylishText>,
          size: '80%',
          children: <PartThumbTable pk={props.pk} setImage={setAndRefresh} />
        });
      },
      icon: <InvenTreeIcon icon='select_image' />
    }
  ];

  return (
    <>
      {downloadImage.modal}
      {deleteUploadImage.modal}

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
            {props.appRole &&
              permissions.hasChangeRole(props.appRole) &&
              hasOverlay && (
                <Overlay
                  color='black'
                  opacity={hovered ? 0.8 : 0}
                  onClick={expandImage}
                >
                  {props.imageActions?.deleteFile && (
                    <Flex
                      onClick={(e) => cancelEvent(e)}
                      pos={'absolute'}
                      right={3}
                      top={3}
                    >
                      <ActionDropdown
                        noindicator={true}
                        icon={
                          <IconDotsVertical
                            color='white'
                            size={30}
                            stroke={1.5}
                          />
                        }
                        actions={imageActions}
                        tooltip='Image Actions'
                        tooltipPosition='top'
                      />
                    </Flex>
                  )}

                  <Flex
                    onClick={(e) => cancelEvent(e)}
                    pos={'absolute'}
                    right={10}
                    bottom={5}
                  >
                    <ActionDropdown
                      noindicator={true}
                      icon={
                        <IconCameraPlus
                          style={{ zIndex: 2 }}
                          color='white'
                          size={30}
                          stroke={1.5}
                        />
                      }
                      actions={newImageActions}
                      tooltip='New Image'
                      tooltipPosition='top'
                    />
                  </Flex>
                </Overlay>
              )}
          </>
        </AspectRatio>
      </Grid.Col>
    </>
  );
}

interface UploadImage {
  pk: string;
  image: string;
  primary?: boolean;
}

interface DetailsImageCarouselProps {
  images: UploadImage[];
  appRole?: UserRoles;
  imageActions?: DetailImageProps['imageActions'];
  apiPath: string;
  model_id: string;
  refresh: () => void;
}

/**
 * Carousel component to display multiple images for a model instance
 */
export function DetailsImageCarousel(
  props: Readonly<DetailsImageCarouselProps>
) {
  const images: UploadImage[] = [...props.images];

  // If there are no images, show one backup image
  if (props.images.length === 0) {
    props.imageActions?.deleteFile;
    props.imageActions?.downloadImage;
    images.push({
      pk: '',
      image: backup_image,
      primary: true
    });
  }

  const onlyOne = images.length === 1;

  return (
    <Carousel
      slideSize='100%'
      align='center'
      loop={!onlyOne}
      withControls={!onlyOne}
      styles={{
        control: {
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.6)' }
        }
      }}
    >
      {images.map((imgObj) => (
        <Carousel.Slide key={imgObj.pk}>
          <DetailsImage
            appRole={props.appRole}
            imageActions={props.imageActions}
            src={imgObj.image}
            apiPath={props.apiPath}
            pk={imgObj.pk}
            model_id={props.model_id}
            primary={imgObj.primary}
            refresh={props.refresh}
          />
        </Carousel.Slide>
      ))}
    </Carousel>
  );
}
