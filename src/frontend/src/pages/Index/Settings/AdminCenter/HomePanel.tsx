import { StylishText } from '@lib/components/StylishText';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  Alert,
  Chip,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { type JSX, useMemo } from 'react';
import { ServerAlert } from '../../../../components/nav/Alerts';
import { QuickAction } from '../../../../components/settings/QuickAction';
import {
  ADMIN_MESSAGE_CLASSIFIERS,
  type AdminMessageClassifier,
  classifierColor,
  classifierLabel,
  useAdminMessages
} from '../../../../hooks/UseAdminMessages';

/**
 * Selector allowing the user to toggle display of each message classifier.
 */
function ClassifierSelector({
  selected,
  onChange,
  counts
}: Readonly<{
  selected: AdminMessageClassifier[];
  onChange: (value: AdminMessageClassifier[]) => void;
  counts: Record<AdminMessageClassifier, number>;
}>): JSX.Element {
  return (
    <Chip.Group
      multiple
      value={selected}
      onChange={(value) => onChange(value as AdminMessageClassifier[])}
    >
      <Group gap='xs' aria-label='admin-message-classifier-selector'>
        {ADMIN_MESSAGE_CLASSIFIERS.map((classifier) => (
          <Chip
            key={classifier}
            value={classifier}
            color={classifierColor(classifier)}
            size='xs'
            aria-label={`admin-message-classifier-${classifier}`}
          >
            {`${classifierLabel(classifier)} (${counts[classifier]})`}
          </Chip>
        ))}
      </Group>
    </Chip.Group>
  );
}

function SystemMessages(): JSX.Element {
  const { messages, isFetching, isError } = useAdminMessages();

  const [selected, setSelected] = useLocalStorage<AdminMessageClassifier[]>({
    key: 'admin-center-message-classifiers',
    defaultValue: ADMIN_MESSAGE_CLASSIFIERS
  });

  const counts = useMemo(() => {
    const result = Object.fromEntries(
      ADMIN_MESSAGE_CLASSIFIERS.map((c) => [c, 0])
    ) as Record<AdminMessageClassifier, number>;

    messages.forEach((msg) => {
      if (msg.classifier in result) result[msg.classifier] += 1;
    });

    return result;
  }, [messages]);

  // Server returns messages sorted by severity
  const visible = useMemo(
    () => messages.filter((msg) => selected.includes(msg.classifier)),
    [messages, selected]
  );

  return (
    <Stack gap='sm'>
      <Group justify='space-between'>
        <ClassifierSelector
          selected={selected}
          onChange={setSelected}
          counts={counts}
        />
        {isFetching && <Loader size='xs' />}
      </Group>
      {isError && (
        <Alert color='red' title={t`Error`}>
          {t`Failed to load system messages`}
        </Alert>
      )}
      {!isError && !isFetching && visible.length === 0 && (
        <Text size='sm' c='dimmed'>
          {t`No messages to display`}
        </Text>
      )}
      <SimpleGrid
        cols={{
          base: 1,
          '600px': 2,
          '1200px': 3
        }}
        type='container'
        spacing='sm'
        aria-label='admin-message-list'
      >
        {visible.map((msg) => (
          <ServerAlert key={msg.key} alert={msg} />
        ))}
      </SimpleGrid>
    </Stack>
  );
}

export default function HomePanel(): JSX.Element {
  return (
    <Stack gap='xs'>
      <Accordion
        multiple
        defaultValue={['quick-actions', 'system-status']}
        variant='contained'
      >
        <Accordion.Item value='quick-actions'>
          <Accordion.Control>
            <StylishText size='md'>
              <Trans>Quick Actions</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <QuickAction />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='system-status'>
          <Accordion.Control>
            <StylishText size='md'>
              <Trans>System Status</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <SystemMessages />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
