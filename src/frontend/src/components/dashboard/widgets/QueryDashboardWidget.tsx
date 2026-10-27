import { Anchor, Group } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';
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
  const modelProperties = ModelInformationDict[modelType];

  const url = useMemo(() => {
    if (!modelProperties.url_overview) {
      return undefined;
    }

    const searchParams = new URLSearchParams();
    Object.entries(params ?? {}).forEach(([key, value]) => {
      searchParams.set(key, String(value));
    });

    const query = searchParams.toString();
    return query
      ? `${modelProperties.url_overview}?${query}`
      : modelProperties.url_overview;
  }, [modelProperties.url_overview, params]);

  const content = (
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
  );

  return url ? (
    <Anchor component={Link} to={url} underline='never'>
      {content}
    </Anchor>
  ) : (
    content
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
