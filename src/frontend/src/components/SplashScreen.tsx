import { BackgroundImage } from '@mantine/core';
import { useEffect } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { generateUrl } from '../functions/urls';
import { useServerApiState } from '../states/ServerApiState';
import { useUserState } from '../states/UserState';

/**
 * Render content within a "splash screen" container.
 */
export default function SplashScreen({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [server, fetchServerApiState] = useServerApiState(
    useShallow((state) => [state.server, state.fetchServerApiState])
  );
  const [checked_login] = useUserState(
    useShallow((state) => [state.login_checked])
  );

  // Fetch server data on mount if no server data is present
  useEffect(() => {
    if (server.server === null) {
      fetchServerApiState();
    }
  }, [server]);

  if (server.customize?.splash && checked_login) {
    return (
      <BackgroundImage src={generateUrl(server.customize.splash)}>
        {children}
      </BackgroundImage>
    );
  } else {
    return <>{children}</>;
  }
}
