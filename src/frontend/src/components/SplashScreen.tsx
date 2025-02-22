import { BackgroundImage } from '@mantine/core';
import { generateUrl } from '../functions/urls';
import { useServerApiState } from '../states/ApiState';

/**
 * Render content within a "splash screen" container.
 */
export default function SplashScreen({
  children
}: {
  children: React.ReactNode;
}) {
  const [server] = useServerApiState((state) => [state.server]);

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
