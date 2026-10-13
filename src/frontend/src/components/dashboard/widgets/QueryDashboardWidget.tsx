import { Anchor, Group } from '@mantine/core';
import { type ReactNode, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
import { navigateToLink } from '@lib/functions/Navigation';
import type { InvenTreeIconType } from '@lib/types/Icons';
import { InvenTreeIcon } from '../../../functions/icons';
import type { DashboardWidgetProps } from '../DashboardWidget';

/**
 * A simple dashboard widget for displaying a link to a particular query
 */
function QueryWidget({
  modelType,
  title,
  icon,
  params
}: Readonly<{
  modelType: ModelType;
  title: string;
  icon?: keyof InvenTreeIconType;
  params: any;
}>): ReactNode {
  const navigate = useNavigate();
  const modelProperties = ModelInformationDict[modelType];

  const onFollowLink = useCallback(
    (event: any) => {
      if (modelProperties.url_overview) {
        let url = modelProperties.url_overview;

        if (params) {
          url += '?';
          for (const key in params) {
            url += `${key}=${params[key]}&`;
          }
        }

        navigateToLink(url, navigate, event);
      }
    },
    [modelProperties, params]
  );

  return (
    <Anchor href='#' onClick={onFollowLink} underline='never'>
      <Group
        gap='xs'
        wrap='nowrap'
        justify='space-between'
        align='center'
        style={{ height: '100%' }}
      >
        <Group gap='xs'>
          <InvenTreeIcon icon={icon ?? modelProperties.icon} />
          <StylishText size='md'>{title}</StylishText>
        </Group>
      </Group>
    </Anchor>
  );
}

/**
 * Construct a dashboard widget descriptor, which displays just a link to a particular query
 */
export default function QueryDashboardWidget({
  label,
  title,
  description,
  modelType,
  enabled = true,
  params
}: {
  label: string;
  title: string;
  description: string;
  modelType: ModelType;
  enabled?: boolean;
  params: any;
}): DashboardWidgetProps {
  return {
    label: label,
    title: title,
    description: description,
    enabled: enabled,
    modelType: modelType,
    minWidth: 2,
    minHeight: 1,
    render: () => (
      <QueryWidget modelType={modelType} title={title} params={params} />
    )
  };
}
