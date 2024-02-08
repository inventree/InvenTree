import { Splide, SplideSlide } from '@splidejs/react-splide';


type GalleryImage = {
    src: string;
    alt?: string;
    title?: string;
};

export default function ImageGallery({
    images,
    title,
    height="400px",
    options={},
}: {
    images: GalleryImage[];
    title?: string;
    height?: string;
    options?: any;
}) {

    const perPage = Math.min(images.length, 3);

    return (
        <Splide
            aria-label={title ?? "Image Gallery"}
            options={{
                type: 'loop',
                perMove: 1,
                perPage: perPage,
                pagination: false,
                autoplay: true,
                gap: '20px',
                height: height,
                fixedHeight: height,
                autoHeight: true,
                autoWidth: false,
                ...options
            }}

            >
            {images.map((image, idx) => (
                <SplideSlide key={idx}>
                    <img src={image.src} alt={image.alt} title={image.title} />
                </SplideSlide>
            ))}
        </Splide>
    );
}