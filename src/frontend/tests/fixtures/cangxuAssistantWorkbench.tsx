import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';
import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { ApiProvider } from '../../src/contexts/ApiContext';
import AssistantWorkbench from '../../src/pages/assistant/AssistantWorkbench';
import { useUserState } from '../../src/states/UserState';
useUserState.setState({ user: { pk: 42, username: '演示用户' } as any });
createRoot(document.getElementById('root')!).render(
  <MantineProvider forceColorScheme='dark'>
    <ApiProvider api={axios.create()} client={new QueryClient()}>
      <MemoryRouter initialEntries={['/assistant/']}>
        <AssistantWorkbench />
      </MemoryRouter>
    </ApiProvider>
  </MantineProvider>
);
