import { BackgroundImage } from '@mantine/core';
import { useEffect } from 'react';
import { generateUrl } from '../functions/urls';
import { useServerApiState } from '../states/ApiState';

/**
 * Render content within a "splash screen" container.
 */
export default function SplashScreen({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [server, fetchServerApiState] = useServerApiState((state) => [
    state.server,
    state.fetchServerApiState
  ]);

  // Fetch server data on mount if no server data is present
  useEffect(() => {
    if (server.server === null) {
      fetchServerApiState();
    }
  }, [server]);

  if (server.customize?.splash) {
    return (
      <BackgroundImage src={generateUrl(server.customize.splash)}>
        {children}
      </BackgroundImage>
    );
  } else {
    return <>{children}</>;
  }
}
