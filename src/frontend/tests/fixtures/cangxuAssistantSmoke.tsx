import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';
import { QueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { ApiProvider } from '../../src/contexts/ApiContext';
import AssistantPage from '../../src/pages/assistant/AssistantPage';
import { useUserState } from '../../src/states/UserState';

useUserState.setState({ user: { pk: 42 } as any });
const dark = new URLSearchParams(location.search).get('theme') === 'dark';
createRoot(document.getElementById('root')!).render(
  <MantineProvider forceColorScheme={dark ? 'dark' : 'light'}>
    <ApiProvider api={axios.create()} client={new QueryClient()}>
      <MemoryRouter
        initialEntries={[
          {
            pathname: '/assistant/',
            state: {
              references: [
                { object_type: 'part', object_id: '12', label: '虚构物料 #12' }
              ]
            }
          }
        ]}
      >
        <AssistantPage />
      </MemoryRouter>
    </ApiProvider>
  </MantineProvider>
);
