
import { ActionIcon } from "@mantine/core";
import { Tooltip } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";
import { t } from "@lingui/macro";
import { useState } from "react";

import { notYetImplemented } from "../../functions/notifications";

export function DownloadAction({
    downloadCallback
} : {
    downloadCallback: (fileFormat: string) => void;
}) {

    const [fileFormat, setFileFormat] = useState<string>('csv');

    // Open modal to select file format
    function download() {

        // TODO: Implement file format selection modal

        notYetImplemented();

        // downloadCallback('csv');
    }

    return <ActionIcon>
            <Tooltip label={t`Download selected data`}>
                <IconDownload onClick={download}/>
            </Tooltip>
        </ActionIcon>;
}
