
import { Image } from "@mantine/core";
import { HoverCard } from "@mantine/core";

import { t } from "@lingui/macro";

import { api } from "../../App";
import { max } from "lodash";

export function Thumbnail({
    src,
    alt = t`Thumbnail`,
    size=24,
} : {
    src: string;
    alt?: string;
    size?: number;
}) {

    // TODO: Use api to determine the correct URL
    let url = "http://localhost:8000" + src;

    // TODO: Use HoverCard to display a larger version of the image

    return <Image
        src={url}
        alt={alt}
        width={size}
        fit="contain"
        radius="xs"
        withPlaceholder
        imageProps={{
            style: {
                maxHeight: size,
            }
        }}
        />;
}