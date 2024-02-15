import { Trans, t } from '@lingui/macro';
import {
  AspectRatio,
  Button,
  Group,
  Image,
  Overlay,
  Paper,
  Text,
  rem,
  useMantineTheme
} from '@mantine/core';
import { Dropzone, FileWithPath, IMAGE_MIME_TYPE } from '@mantine/dropzone';
import { useHover } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useMemo, useState } from 'react';

import { api } from '../../App';
import { InvenTreeIcon } from '../../functions/icons';
import { notYetImplemented } from '../../functions/notifications';
import { apiUrl } from '../../states/ApiState';
import { ActionButton } from '../buttons/ActionButton';
import { ApiImage } from '../images/ApiImage';

/**
 * Props for detail image
 */
export type DetailImageProps = {
  src: string;
  endpoint: string;
  pk: number;
  allowUpload?: boolean;
  allowDownload?: boolean;
  allowSelect?: boolean;
  allowDelete?: boolean;
  refresh: () => void;
};

// Image is expected to be 1:1 square, so only 1 dimension is needed
const IMAGE_DIMENSION = 256;

/**
 * Modal used for removing/deleting the current image relation
 */
function RemoveImage(props: DetailImageProps) {
  modals.openConfirmModal({
    title: t`Remove Image`,
    children: (
      <Text size="sm">
        <Trans>Remove the associated image from this item?</Trans>
      </Text>
    ),
    labels: { confirm: t`Remove`, cancel: t`Cancel` },
    onConfirm: async () => {
      api
        .patch(apiUrl(props.endpoint, props.pk), {
          image: null
        })
        .then(() => {
          props.refresh();
        });
    }
  });
}

/**
 * Modal used for uploading a new image
 */
function UploadModal({ props }: { props: DetailImageProps }) {
  const [file1, setFile] = useState<FileWithPath | null>(null);
  let uploading = false;

  // Components to show in the Dropzone when no file is selected
  const noFileIdle = (
    <Group>
      <InvenTreeIcon icon="photo" iconProps={{ size: '3.2rem', stroke: 1.5 }} />
      <div>
        <Text size="xl" inline>
          <Trans>Drag and drop to upload</Trans>
        </Text>
        <Text size="sm" color="dimmed" inline mt={7}>
          <Trans>Click to select image file</Trans>
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

    api.patch(apiUrl(props.endpoint, props.pk), formData).then((response) => {
      modals.close('upload-image');
      props.refresh();
    });
  };

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
                color: 'green'
              }}
            />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <InvenTreeIcon
              icon="reject"
              iconProps={{
                size: '3.2rem',
                stroke: 1.5,
                color: 'red'
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

/*
 * Construct a group of buttons which appear when the image is hovered
 */
function ImageButtonGroup({ props }: { props: DetailImageProps }) {
  return (
    <>
      <Group
        position="left"
        spacing="xs"
        style={{ zIndex: 2, position: 'absolute', top: '10px', left: '10px' }}
      >
        {props.allowSelect && (
          <ActionButton
            icon={<InvenTreeIcon icon="select_image" />}
            tooltip={t`Select Existing Image`}
            variant="filled"
            size="lg"
            tooltipAlignment="top"
            onClick={() => notYetImplemented()}
          />
        )}
        {props.allowDownload && (
          <ActionButton
            icon={<InvenTreeIcon icon="download" />}
            tooltip={t`Download Image`}
            variant="filled"
            size="lg"
            tooltipAlignment="top"
            onClick={() => notYetImplemented()}
          />
        )}
        {props.allowUpload && (
          <ActionButton
            icon={<InvenTreeIcon icon="upload" />}
            tooltip={t`Upload Image`}
            variant="filled"
            size="lg"
            tooltipAlignment="top"
            onClick={() => {
              modals.open({
                title: t`Upload Image`,
                modalId: 'upload-image',
                children: <UploadModal props={props} />
              });
            }}
          />
        )}
        {props.allowDelete && props.src && (
          <ActionButton
            icon={<InvenTreeIcon icon="delete" iconProps={{ color: 'red' }} />}
            tooltip={t`Delete image`}
            variant="filled"
            size="lg"
            tooltipAlignment="top"
            onClick={() => RemoveImage(props)}
          />
        )}
      </Group>
    </>
  );
}

/**
 * Renders an image with action buttons for display on Details panels
 */
export function DetailsImage(props: DetailImageProps) {
  // Displays a group of ActionButtons on hover

  const { hovered, ref } = useHover();
  const hasActions = props.allowDelete || props.allowUpload;

  const img: string = useMemo(() => {
    return props.src || '/static/img/blank_image.png';
  }, [props.src]);

  return (
    <AspectRatio ref={ref} ratio={1} maw={IMAGE_DIMENSION} mx="auto">
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
      {hasActions && hovered && (
        <Overlay opacity={0.35} zIndex={1} radius="sm">
          <ImageButtonGroup props={props} />
        </Overlay>
      )}
    </AspectRatio>
  );
}
