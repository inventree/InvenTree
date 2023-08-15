import { Trans } from '@lingui/macro';
import {
  Badge,
  Group,
  HoverCard,
  List,
  SimpleGrid,
  Text,
  ThemeIcon,
  Tooltip
} from '@mantine/core';
import { IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { forwardRef } from 'react';

import { useApiState } from '../../../states/ApiState';
import { UserRenderer } from '../../renderer/UserRenderer';
import { ApprovalAddComponent } from './ApprovalAddComponent';

function DecisionComponent({ decision }: { decision: any }) {
  const icon = decision.decision ? (
    <IconCircleCheck size="1rem" />
  ) : (
    <IconCircleX size="1rem" />
  );
  const icon_color = decision.decision ? 'green' : 'red';
  return (
    <List.Item
      icon={
        <ThemeIcon color={icon_color} size={24} radius="xl">
          {icon}
        </ThemeIcon>
      }
    >
      <Tooltip label={decision.date}>
        <Group>
          <UserRenderer detail={decision.user_detail} /> {decision.comment}
        </Group>
      </Tooltip>
    </List.Item>
  );
}

export function ExistingApprovalComponent({
  refetch,
  data
}: {
  refetch: () => void;
  data: any;
}) {
  const user_id = useApiState((state) => state.user?.id);

  const FinalState = () => {
    if (data.finalised == true)
      return (
        <Badge color="green" variant="outline">
          <Trans>Finalised</Trans>
        </Badge>
      );
    return (
      <Badge color="yellow" variant="outline">
        <Trans>Not finalised</Trans>
      </Badge>
    );
  };
  let status_color = 'yellow';
  switch (data.status) {
    case 20:
      status_color = 'green';
      break;
    case 30:
      status_color = 'red';
      break;
    default:
      break;
  }
  const my_decision = data.decisions.find(
    (decision: any) => decision.user == user_id
  );

  const MainApprovalComponent = forwardRef<HTMLDivElement>((props, ref) => (
    <div ref={ref} {...props}>
      <Group spacing={'xs'} mb={8}>
        <Badge color={status_color} variant="light">
          {data.status_text}
        </Badge>
        <FinalState />
      </Group>
      {data.decisions.length == 0 ? (
        <Text c="dimmed" ta="right">
          <Trans>No Decisions yet</Trans>
        </Text>
      ) : (
        <List>
          {data.decisions.map((decision: any) => (
            <DecisionComponent key={decision.id} decision={decision} />
          ))}
        </List>
      )}
      {data.finalised == false && my_decision === undefined && (
        <ApprovalAddComponent approvalPK={data.id} refetch={refetch} />
      )}
    </div>
  ));

  const DetailApprovalComponent = () => (
    <Text size="sm">
      <SimpleGrid cols={2} spacing="xs">
        <div>
          <Trans>Name</Trans>
        </div>
        <div>
          <Text>{data.name}</Text>
        </div>

        {data.description && (
          <>
            <div>
              <Trans>Description</Trans>
            </div>
            <div>{data.description}</div>
          </>
        )}

        {data.reference && (
          <>
            <div>
              <Trans>Reference</Trans>
            </div>
            <div>{data.reference}</div>
          </>
        )}

        <div>
          <Trans>Creation date</Trans>
        </div>
        <div>{data.creation_date}</div>

        <div>
          <Trans>Created by</Trans>
        </div>
        <div>
          <UserRenderer detail={data.created_by_detail} />
        </div>

        <div>
          <Trans>Modification date</Trans>
        </div>
        <div>{data.modified_date}</div>

        <div>
          <Trans>Modified by</Trans>
        </div>
        <div>
          <UserRenderer detail={data.modified_by_detail} />
        </div>

        {data.finalised == true && (
          <>
            <div>
              <Trans>Finalisation date</Trans>
            </div>
            <div>{data.finalised_date}</div>

            <div>
              <Trans>Finalised by</Trans>
            </div>
            <div>
              <UserRenderer detail={data.finalised_by_detail} />
            </div>
          </>
        )}
      </SimpleGrid>
    </Text>
  );

  return (
    <HoverCard shadow="md" withArrow openDelay={200} closeDelay={400}>
      <HoverCard.Target>
        <MainApprovalComponent />
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <DetailApprovalComponent />
      </HoverCard.Dropdown>
    </HoverCard>
  );
}
