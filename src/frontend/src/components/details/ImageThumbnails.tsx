import { type DetailImageProps, DetailsImage } from './DetailsImage';

export function ImageThumbnails(props: Readonly<DetailImageProps>) {
  return (
    <>
      <DetailsImage
        appRole={props.appRole}
        imageActions={{
          selectExisting: true,
          downloadImage: true,
          uploadFile: true,
          deleteFile: true
        }}
        src={props.src}
        apiPath={props.apiPath}
        refresh={props.refresh}
        pk={props.pk}
      />
    </>
  );
}
