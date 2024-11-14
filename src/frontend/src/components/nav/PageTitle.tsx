import { useEffect, useMemo } from 'react';
import { useGlobalSettingsState } from '../../states/SettingsState';

/**
 * Component to set the page title
 */
export default function PageTitle({
  title,
  subtitle
}: Readonly<{
  title?: string;
  subtitle?: string;
}>) {
  const globalSettings = useGlobalSettingsState();

  const pageTitle = useMemo(() => {
    const instanceName = globalSettings.getSetting(
      'INVENTREE_INSTANCE',
      'InvenTree'
    );
    const useInstanceName = globalSettings.isSet(
      'INVENTREE_INSTANCE_TITLE',
      false
    );

    let data = '';

    if (title) {
      data += title;
    }

    if (subtitle) {
      data += ` - ${subtitle}`;
    }

    if (useInstanceName) {
      data = `${instanceName} | ${data}`;
    }

    if (!data) {
      // Backup: No title provided
      data = instanceName;
    }

    return data;
  }, [title, subtitle, globalSettings]);

  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);

  return <title>{pageTitle}</title>;
}
