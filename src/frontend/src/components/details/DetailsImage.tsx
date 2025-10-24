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
import { useQuery } from '@tanstack/react-query';
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
  content_type?: ModelType.part | ModelType.company;
  useGridCol?: boolean;
};

/**
 * Actions for add image in Detail Images (Only for multiple details images).
 * If true, the button type will be visible
 * @param {boolean} selectExisting - PART ONLY. Allows selecting existing images as part image
 * @param {boolean} uploadNewImage - PART ONLY. Allows uploading a new image.
 */
export type AddImageButtonProps = {
  selectExisting?: boolean;
  uploadNewImage?: boolean;
};

/**
 * Actions for edit image in Detail Images.
 * If true, the button type will be visible
 * @param {boolean} downloadImage - Allows downloading image from a remote URL
 * @param {boolean} replaceImage - PART ONLY. Allows replacing the current image with a new file
 * @param {boolean} deleteImage - Allows deleting the current image
 * @param {boolean} setAsPrimary - PART ONLY. Allows setting the current image as primary image
 */
export type EditImageButtonProps = {
  downloadImage?: boolean;
  replaceImage?: boolean;
  deleteImage?: boolean;
  setAsPrimary?: boolean;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

// Image to display if instance has no image
const backup_image = '/static/img/blank_image.png';

/**
 * Modal used for uploading a new image
 */
function UploadModal({
  setImage,
  object_id,
  content_type
}: Readonly<{
  setImage: (image: string) => void;
  object_id: string;
  content_type: string;
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
    formData.append('content_type', content_type);
    formData.append('object_id', object_id);

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
  pk,
  addActions,
  editActions,
  content_type,
  setAsPrimary,
  downloadImage,
  setAndRefresh,
  deleteUploadImage
}: Readonly<{
  pk: string;
  addActions?: AddImageButtonProps;
  editActions?: EditImageButtonProps;
  content_type?: string;
  setAsPrimary: () => void;
  downloadImage: () => void;
  setAndRefresh: (image: string) => void;
  deleteUploadImage: any;
}>) {
  const globalSettings = useGlobalSettingsState();

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
      name: 'Replace image',
      onClick: (e) => {
        cancelEvent(e);
        modals.open({
          title: <StylishText size='xl'>{t`Replace Image`}</StylishText>,
          children: (
            <UploadModal
              object_id={pk!}
              content_type={String(content_type)}
              setImage={setAndRefresh}
            />
          )
        });
      },
      icon: <InvenTreeIcon icon='upload' />,
      hidden: !editActions?.replaceImage
    },
    {
      name: 'Download remote image',
      onClick: (event: any) => {
        cancelEvent(event);
        downloadImage();
      },
      icon: <InvenTreeIcon icon='download' />,
      hidden:
        !editActions?.downloadImage ||
        !globalSettings.isSet('INVENTREE_DOWNLOAD_FROM_URL')
    },

    {
      name: 'Delete image',
      onClick: (event: any) => {
        cancelEvent(event);
        deleteUploadImage.open();
      },
      icon: <InvenTreeIcon icon='delete' iconProps={{ color: 'red' }} />,
      hidden: !editActions?.deleteImage
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
              content_type={String(content_type)}
              object_id={pk!}
              setImage={setAndRefresh}
            />
          )
        });
      },
      icon: <InvenTreeIcon icon='upload' />,
      hidden: !addActions?.uploadNewImage
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

  const downloadImage = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.upload_image_list),
    title: t`Download Image`,
    fields: {
      remote_image: {},
      object_id: { hidden: true, value: props.pk },
      content_type: { hidden: true, value: props.content_type }
    },
    timeout: 10000,
    submitText: t`Download`,
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
    ignorePermissionCheck: true,
    pk: props.image_id,
    title: t`Delete Image`,
    onFormSuccess: () => {
      setAndRefresh(backup_image);
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
      props.EditImageActions?.deleteImage ||
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

  const imageContent = (
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
                content_type={props.content_type}
                downloadImage={downloadImage.open}
                setAndRefresh={setAndRefresh}
                setAsPrimary={setAsPrimary}
              />
            </Overlay>
          )}
      </>
    </AspectRatio>
  );

  return (
    <>
      {downloadImage.modal}
      {deleteUploadImage.modal}

      {props.useGridCol !== false ? (
        <Grid.Col span={{ base: 12, sm: 4 }}>{imageContent}</Grid.Col>
      ) : (
        imageContent
      )}
    </>
  );
}

interface UploadImage {
  pk: string;
  image: string;
  primary?: boolean;
}

interface DetailsImageCarouselProps {
  appRole?: UserRoles;
  apiPath: string;
  object_id: string;
  content_model: ModelType;
  refresh?: () => void;
}

/**
 * Carousel component to display multiple images for a model instance
 */
export function MultipleDetailsImage(
  props: Readonly<DetailsImageCarouselProps>
) {
  const imageQuery = useQuery<UploadImage[]>({
    queryKey: [ApiEndpoints.upload_image_list, props.object_id],
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.upload_image_list), {
          params: {
            content_model: props.content_model,
            object_id: props.object_id
          }
        })
        .then((response) => {
          // Return the data directly, or fallback to backup image
          if (!response.data || response.data.length === 0) {
            return [
              {
                pk: 'backup',
                image: backup_image,
                primary: true
              }
            ];
          }
          return response.data;
        });
    }
  });

  const config = useMemo(() => {
    const images = imageQuery.data || [];

    return {
      onlyOne: images.length === 1,
      startSlide: Math.max(
        0,
        images.findIndex((img) => img.primary)
      ),
      addImageActions: {
        selectExisting: true,
        uploadNewImage: true
      },
      editImageActions: {
        deleteImage: !(images.length === 1 && images[0]?.pk === 'backup'),
        downloadImage: false,
        setAsPrimary: images.length > 0,
        replaceImage: false
      }
    };
  }, [imageQuery.data]);

  return (
    <Grid.Col span={{ base: 12, sm: 4 }}>
      <Carousel
        slideSize='100%'
        emblaOptions={{
          loop: !config.onlyOne,
          align: 'center'
        }}
        initialSlide={config.startSlide}
        withControls={!config.onlyOne}
        previousControlProps={{
          style: {
            transform: 'translateX(-45%)',
            color: 'white',
            backgroundColor: 'rgba(0, 0, 0, 0.4)'
          }
        }}
        nextControlProps={{
          style: {
            transform: 'translateX(45%)',
            color: 'white',
            backgroundColor: 'rgba(0, 0, 0, 0.6)'
          }
        }}
        styles={{
          control: {
            '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.6)' }
          }
        }}
      >
        {!imageQuery.isFetching &&
          imageQuery.data &&
          imageQuery.data.map((imgObj: UploadImage, index: number) => (
            <Carousel.Slide key={index}>
              <DetailsImage
                appRole={props.appRole}
                AddImageActions={config.addImageActions}
                EditImageActions={config.editImageActions}
                src={imgObj.image}
                image_id={imgObj.pk}
                pk={props.object_id}
                primary={imgObj.primary}
                content_type={ModelType.part}
                refresh={props.refresh}
                useGridCol={false}
              />
            </Carousel.Slide>
          ))}
      </Carousel>
    </Grid.Col>
  );
}
