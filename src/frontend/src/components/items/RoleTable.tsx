import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Button,
  Checkbox,
  Group,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconReload } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '../../App';

export interface RuleSet {
  pk?: number;
  group?: number;
  name: string;
  label: string;
  can_view: boolean;
  can_add: boolean;
  can_change: boolean;
  can_delete: boolean;
  edited?: boolean;
}

export function RoleTable({
  roles,
  editable = false
}: {
  roles: RuleSet[];
  editable?: boolean;
}) {
  const [rulesets, setRulesets] = useState<RuleSet[]>(roles);

  useEffect(() => {
    setRulesets(roles);
  }, [roles]);

  const edited = useMemo(() => rulesets.some((r) => r.edited), [rulesets]);

  // Ensure the rulesets are always displayed in the same order
  const sortedRulesets = useMemo(() => {
    return rulesets.sort((a, b) => (a.label > b.label ? 1 : -1));
  }, [rulesets]);

  // Change the edited state of the ruleset
  const onToggle = useCallback(
    (rule: RuleSet, field: string) => {
      if (!editable) {
        return;
      }
      setRulesets((prev) => {
        const updated = prev.map((r) => {
          if (r.pk === rule.pk) {
            return {
              ...r,
              [field]: !(r as any)[field],
              edited: true
            };
          }
          return r;
        });
        return updated;
      });
    },
    [editable]
  );

  const onSave = async (rulesets: RuleSet[]) => {
    if (!editable) {
      return;
    }

    notifications.show({
      id: 'group-roles-update',
      title: t`Updating`,
      message: t`Updating group roles`,
      loading: true,
      color: 'blue',
      autoClose: false
    });

    for (const ruleset of rulesets.filter((r) => r.edited)) {
      await api
        .patch(apiUrl(ApiEndpoints.ruleset_list, ruleset.pk), {
          can_view: ruleset.can_view,
          can_add: ruleset.can_add,
          can_change: ruleset.can_change,
          can_delete: ruleset.can_delete
        })
        .then(() => {
          // Mark this ruleset as "not edited"
          setRulesets((prev) => {
            const updated = prev.map((r) => {
              if (r.pk === ruleset.pk) {
                return {
                  ...r,
                  edited: false
                };
              }
              return r;
            });
            return updated;
          });
        })
        .catch((error) => {
          console.error(error);
        });
    }

    notifications.update({
      id: 'group-roles-update',
      title: t`Updated`,
      message: t`Group roles updated`,
      autoClose: 2000,
      color: 'green',
      icon: <IconCircleCheck />,
      loading: false
    });
  };

  return (
    <>
      <Stack gap='xs'>
        <Table striped withColumnBorders withRowBorders withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>
                <Text fw={700}>
                  <Trans>Role</Trans>
                </Text>
              </Table.Th>
              <Table.Th>
                <Text fw={700}>
                  <Trans>View</Trans>
                </Text>
              </Table.Th>
              <Table.Th>
                <Text fw={700}>
                  <Trans>Change</Trans>
                </Text>
              </Table.Th>
              <Table.Th>
                <Text fw={700}>
                  <Trans>Add</Trans>
                </Text>
              </Table.Th>
              <Table.Th>
                <Text fw={700}>
                  <Trans>Delete</Trans>
                </Text>
              </Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {sortedRulesets.map((rule) => (
              <Table.Tr key={rule.pk ?? rule.name}>
                <Table.Td>
                  <Group gap='xs'>
                    <Text>{rule.label}</Text>
                    {rule.edited && <Text>*</Text>}
                  </Group>
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    disabled={!editable}
                    checked={rule.can_view}
                    onChange={() => onToggle(rule, 'can_view')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    disabled={!editable}
                    checked={rule.can_change}
                    onChange={() => onToggle(rule, 'can_change')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    disabled={!editable}
                    checked={rule.can_add}
                    onChange={() => onToggle(rule, 'can_add')}
                  />
                </Table.Td>
                <Table.Td>
                  <Checkbox
                    disabled={!editable}
                    checked={rule.can_delete}
                    onChange={() => onToggle(rule, 'can_delete')}
                  />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
        {editable && (
          <Group justify='right'>
            <Tooltip label={t`Reset group roles`} disabled={!edited}>
              <Button
                color='red'
                onClick={() => {
                  setRulesets(roles);
                }}
                disabled={!edited}
                leftSection={<IconReload />}
              >
                {t`Reset`}
              </Button>
            </Tooltip>
            <Tooltip label={t`Save group roles`} disabled={!edited}>
              <Button
                color='green'
                onClick={() => {
                  onSave(rulesets);
                }}
                disabled={!edited}
                leftSection={<IconCircleCheck />}
              >
                {t`Save`}
              </Button>
            </Tooltip>
          </Group>
        )}
      </Stack>
    </>
  );
}
