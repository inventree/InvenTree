import { lazy } from 'react';

import { Loadable } from '../../functions/loading';
import { useImporterState } from '../../states/ImporterState';

// Lazy loaded: this pulls in InvenTreeTable (and its own sizeable
// dependency tree) via ImportDataSelector, but an import session is only
// ever open for a small fraction of page loads - the isOpen/sessionId
// check below runs first regardless, so nothing here is fetched at all
// unless the user actually opens the importer.
const ImporterDrawer = Loadable(lazy(() => import('./ImporterDrawer')));

export default function GlobalImporterDrawer() {
  const isOpen = useImporterState((state) => state.isOpen);
  const sessionId = useImporterState((state) => state.sessionId);
  const customFields = useImporterState((state) => state.customFields);
  const closeImporter = useImporterState((state) => state.closeImporter);

  if (!isOpen || sessionId === null) {
    return null;
  }

  return (
    <ImporterDrawer
      sessionId={sessionId}
      opened={isOpen}
      onClose={closeImporter}
      customFields={customFields}
    />
  );
}
