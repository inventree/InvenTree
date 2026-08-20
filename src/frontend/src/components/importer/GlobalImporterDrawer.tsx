import { useImporterState } from '../../states/ImporterState';
import ImporterDrawer from './ImporterDrawer';

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
