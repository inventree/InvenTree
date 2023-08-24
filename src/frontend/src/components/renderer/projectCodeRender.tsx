import { Anchor, Tooltip } from '@mantine/core';

import { ApiPaths, url } from '../../states/ApiState';

export function projectCodeRender(record: any) {
  const project = record.project_code_detail;
  return (
    project && (
      <Tooltip label={project.description} position="bottom">
        <Anchor href={url(ApiPaths.frontend_project, project.pk)}>
          {project.code}
        </Anchor>
      </Tooltip>
    )
  );
}
