import { Trans, t } from '@lingui/macro';
import { Badge, Tooltip } from '@mantine/core';

import { InvenTreeIcon, InvenTreeIconType } from '../../functions/icons';

/**
 * Fetches and wraps an InvenTreeIcon in a flex div
 * @param icon name of icon
 *
 */
function PartIcon(icon: InvenTreeIconType) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
      <InvenTreeIcon icon={icon} />
    </div>
  );
}

/**
 * Generates a table cell with Part icons.
 * Only used for Part Model Details
 */
export function PartIcons({ part }: { part: any }) {
  return (
    <td colSpan={2}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {!part.active && (
          <Tooltip label={t`Part is not active`}>
            <Badge color="red" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="inactive" iconProps={{ size: 19 }} />{' '}
                <Trans>Inactive</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
        {part.template && (
          <Tooltip
            label={t`Part is a template part (variants can be made from this part)`}
            children={PartIcon('template')}
          />
        )}
        {part.assembly && (
          <Tooltip
            label={t`Part can be assembled from other parts`}
            children={PartIcon('assembly')}
          />
        )}
        {part.component && (
          <Tooltip
            label={t`Part can be used in assemblies`}
            children={PartIcon('component')}
          />
        )}
        {part.trackable && (
          <Tooltip
            label={t`Part stock is tracked by serial number`}
            children={PartIcon('trackable')}
          />
        )}
        {part.purchaseable && (
          <Tooltip
            label={t`Part can be purchased from external suppliers`}
            children={PartIcon('purchaseable')}
          />
        )}
        {part.saleable && (
          <Tooltip
            label={t`Part can be sold to customers`}
            children={PartIcon('saleable')}
          />
        )}
        {part.virtual && (
          <Tooltip label={t`Part is virtual (not a physical part)`}>
            <Badge color="yellow" variant="filled">
              <div
                style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
              >
                <InvenTreeIcon icon="virtual" iconProps={{ size: 18 }} />{' '}
                <Trans>Virtual</Trans>
              </div>
            </Badge>
          </Tooltip>
        )}
      </div>
    </td>
  );
}
