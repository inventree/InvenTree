
import Zoom from 'react-medium-image-zoom';
import 'react-medium-image-zoom/dist/styles.css';


// Function to ensure that the required file actually exists
function checkImage(path: string) {

    if (!path) {
        return;
    }
    
    require(`@site/static${path}`);
}


export default function Thumnbnail({
    src,
    title,
    height="240px",
}: {
    src: string,
    title?: string;
    height?: string;
}) {

    checkImage(src);

    return (
        <Zoom>
            <div className='thumbnail-container'>
                <img src={src} alt={title ?? ""} height={height} />
            </div>
        </Zoom> 
    )
}
