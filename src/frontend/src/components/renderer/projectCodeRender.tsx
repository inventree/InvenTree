import { Anchor, Tooltip } from '@mantine/core';

export function projectCodeRender(record: any) {
  const project = record.project_code_detail;
  return (
    project && (
      <Tooltip label={project.description} position="bottom">
        <Anchor href={`/project/${project.pk}`}>{project.code}</Anchor>
      </Tooltip>
    )
  );
}
