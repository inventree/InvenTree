import { Trans } from '@lingui/macro'

export function ErrorItem({ id, error }: { id: string, error?: any }) {
    const error_message = error?.message || error?.toString() || <Trans>Unknown error</Trans>;
    return (<>
        <p><Trans>An error occured:</Trans></p>
        {error_message}
    </>);
}
