import type { UserRoles } from '@lib/enums/Roles';
import { cancelEvent } from '@lib/functions/Events';
import { ApiEndpoints, ModelType, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Carousel } from '@mantine/carousel';
import {
  AspectRatio,
  Button,
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
import { showNotification } from '@mantine/notifications';
import { IconCameraPlus, IconDotsVertical } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import { api } from '../../App';
import { InvenTreeIcon } from '../../functions/icons';
import { showApiErrorMessage } from '../../functions/notifications';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { PartThumbTable } from '../../tables/part/PartThumbTable';
import { vars } from '../../theme';
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
  refresh?: () => void;
  AddImageActions?: AddImageButtonProps;
  EditImageActions?: EditImageButtonProps;
  pk: string;
  image_id?: string;
  model_type?: ModelType.part | ModelType.company;
};

/**
 * Actions for add image in Detail Images (Only for multiple details images).
 * If true, the button type will be visible
 * @param {boolean} selectExisting - PART ONLY. Allows selecting existing images as part image
 * @param {boolean} uploadNewFile - PART ONLY. Allows uploading a new image.
 */
export type AddImageButtonProps = {
  selectExisting?: boolean;
  uploadNewFile?: boolean;
};

/**
 * Actions for edit image in Detail Images.
 * If true, the button type will be visible
 * @param {boolean} downloadImage - Allows downloading image from a remote URL
 * @param {boolean} uploadFile - PART ONLY. Allows replacing the current image with a new file
 * @param {boolean} deleteFile - Allows deleting the current image
 * @param {boolean} setAsPrimary - PART ONLY. Allows setting the current image as primary image
 */
export type EditImageButtonProps = {
  downloadImage?: boolean;
  uploadFile?: boolean;
  deleteFile?: boolean;
  setAsPrimary?: boolean;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

// Image to display if instance has no image
const backup_image = '/static/img/blank_image.png';

// TODO: change model_id and pk name (reza)
/**
 * Modal used for uploading a new image
 */
function UploadModal({
  setImage,
  model_id,
  model_type
}: Readonly<{
  setImage: (image: string) => void;
  model_id: string;
  model_type: string;
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
    formData.append('model_type', model_type);
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
  addActions = {},
  editActions = {},
  pk,
  model_type,
  setAndRefresh,
  setAsPrimary,
  downloadImage,
  deleteUploadImage
}: Readonly<{
  addActions?: AddImageButtonProps;
  editActions?: EditImageButtonProps;
  pk: string;
  model_type?: string;
  setAndRefresh: (image: string) => void;
  setAsPrimary: () => void;
  downloadImage: () => void;
  deleteUploadImage: any;
}>) {
  const globalSettings = useGlobalSettingsState();
  const hasImage: boolean = Boolean(editActions?.deleteFile);

  const editImageActions: ActionDropdownItem[] = [
    {
      name: 'Set as primary',
      onClick: (event: any) => {
        cancelEvent(event);
        setAsPrimary();
      },
      icon: <InvenTreeIcon icon='complete' />,
      hidden: !editActions?.setAsPrimary
    },
    {
      name: hasImage ? 'Replace image' : 'Upload image',
      onClick: (e) => {
        cancelEvent(e);
        modals.open({
          title: (
            <StylishText size='xl'>
              {hasImage ? t`Replace Image` : t`Upload Image`}
            </StylishText>
          ),
          children: (
            <UploadModal
              model_id={pk!}
              model_type={String(model_type)}
              setImage={setAndRefresh}
            />
          )
        });
      },
      icon: <InvenTreeIcon icon='upload' />,
      hidden: !editActions?.uploadFile
    },
    {
      name: 'Download remote image',
      onClick: (event: any) => {
        cancelEvent(event);
        downloadImage();
      },
      icon: <InvenTreeIcon icon='download' />,
      hidden:
        !editActions?.downloadImage &&
        !globalSettings.isSet('INVENTREE_DOWNLOAD_FROM_URL')
    },

    {
      name: 'Delete image',
      onClick: (event: any) => {
        cancelEvent(event);
        deleteUploadImage.open();
      },
      icon: <InvenTreeIcon icon='delete' iconProps={{ color: 'red' }} />,
      hidden: !editActions?.deleteFile
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
            <UploadModal
              model_type={String(model_type)}
              model_id={pk!}
              setImage={setAndRefresh}
            />
          )
        });
      },
      icon: <InvenTreeIcon icon='upload' />,
      hidden: !addActions?.uploadNewFile
    },
    {
      name: 'Select from existing images',
      onClick: (event: any) => {
        cancelEvent(event);
        modals.open({
          title: <StylishText size='xl'>{t`Select Image`}</StylishText>,
          size: '80%',
          children: (
            <PartThumbTable
              pk={pk!}
              onSuccess={(image) => {
                setAndRefresh(image);
                showNotification({
                  title: t`Image set`,
                  message: t`Image has been set successfully`,
                  color: 'green'
                });
              }}
            />
          )
        });
      },
      icon: <InvenTreeIcon icon='select_image' />,
      hidden: !addActions?.selectExisting
    }
  ];

  return (
    <>
      <Flex onClick={(e) => cancelEvent(e)} pos={'absolute'} right={3} top={3}>
        <ActionDropdown
          noindicator={true}
          icon={<IconDotsVertical color='white' size={30} stroke={1.5} />}
          actions={editImageActions}
          tooltip='Image Actions'
          tooltipPosition='top'
        />
      </Flex>

      <Flex
        onClick={(e) => cancelEvent(e)}
        pos={'absolute'}
        right={0}
        bottom={5}
      >
        <ActionDropdown
          menuPosition='top-end'
          noindicator={true}
          icon={
            <IconCameraPlus
              style={{ zIndex: 2, marginRight: 10 }}
              color='white'
              size={30}
              stroke={1.5}
            />
          }
          actions={newImageActions}
          tooltip='Add New Image'
          tooltipPosition='bottom'
        />
      </Flex>
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

  const url = apiUrl(ApiEndpoints.upload_image_list, props.image_id);

  const downloadImage = useCreateApiFormModal({
    url: url,
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
    pk: props.image_id,
    title: t`Delete Image`,
    onFormSuccess: () => {
      props.refresh?.();
    }
  });

  const setAsPrimary = () => {
    const url = apiUrl(ApiEndpoints.upload_image_list, props.image_id);

    api
      .patch(url, { primary: true })
      .then((response) => {
        setImg(response.data.image);
        showNotification({
          title: t`Image Updated`,
          message: t`Image has been set as primary`,
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

    props.refresh?.();
  };

  const hasOverlay: boolean = useMemo(() => {
    return (
      props.AddImageActions?.selectExisting ||
      props.EditImageActions?.deleteFile ||
      props.EditImageActions?.uploadFile ||
      false
    );
  }, [props.AddImageActions]);

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
                  <ImageActionButtons
                    deleteUploadImage={deleteUploadImage}
                    addActions={props.AddImageActions}
                    editActions={props.EditImageActions}
                    pk={props.pk}
                    model_type={props.model_type}
                    downloadImage={downloadImage.open}
                    setAndRefresh={setAndRefresh}
                    setAsPrimary={setAsPrimary}
                  />
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
  addImageActions?: DetailImageProps['AddImageActions'];
  editImageActions?: DetailImageProps['EditImageActions'];
  apiPath: string;
  model_id: string;
  refresh?: () => void;
}

/**
 * Carousel component to display multiple images for a model instance
 */
export function MultipleDetailsImage(
  props: Readonly<DetailsImageCarouselProps>
) {
  const images: UploadImage[] = [...props.images];

  // If there are no images, show one backup image
  if (props.images.length === 0) {
    images.push({
      pk: '',
      image: backup_image,
      primary: true
    });
  }

  const onlyOne = images.length === 1;

  const primaryIndex = images.findIndex((img) => img.primary);
  // if none are marked primary, fallback to 0
  const startSlide = primaryIndex >= 0 ? primaryIndex : 0;

  return (
    <Carousel
      slideSize='100%'
      align='center'
      loop={!onlyOne}
      initialSlide={startSlide}
      withControls={!onlyOne}
      styles={{
        control: {
          color: 'white',
          backgroundColor: 'rgba(0, 0, 0, 0.4)',
          '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.6)' }
        }
      }}
    >
      {images.map((imgObj) => (
        <Carousel.Slide key={imgObj.pk}>
          <DetailsImage
            appRole={props.appRole}
            AddImageActions={props.addImageActions}
            EditImageActions={props.editImageActions}
            src={imgObj.image}
            image_id={imgObj.pk}
            pk={props.model_id}
            primary={imgObj.primary}
            model_type={ModelType.part}
            refresh={props.refresh}
          />
        </Carousel.Slide>
      ))}
    </Carousel>
  );
}
