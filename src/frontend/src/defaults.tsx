import { Trans } from '@lingui/macro';
import { Image, MantineSize, Text } from '@mantine/core';

import { MenuLinkItem } from './components/nav/MegaHoverMenu';
import { HostList } from './context/states';

export const defaultHostList: HostList = {
  'mantine-u56l5jt85': {
    host: 'https://demo.inventree.org/api/',
    name: 'InvenTree Demo'
  },
  'mantine-g8t1zrj50': {
    host: 'https://sample.app.invenhost.com/api/',
    name: 'InvenHost: Sample'
  },
  'mantine-cqj63coxn': {
    host: 'http://localhost:8000/api/',
    name: 'Localhost'
  }
};
export const defaultHostKey = 'mantine-cqj63coxn';

export const tabs = [{ text: <Trans>Home</Trans>, name: 'home' }];

export const links = [
  {
    link: 'https://inventree.org/',
    label: <Trans>Website</Trans>,
    key: 'website'
  },
  {
    link: 'https://github.com/invenhost/InvenTree',
    label: <Trans>GitHub</Trans>,
    key: 'github'
  },
  {
    link: 'https://demo.inventree.org/',
    label: <Trans>Demo</Trans>,
    key: 'demo'
  }
];

export const menuItems: MenuLinkItem[] = [
  {
    title: 'Open source',
    description: 'This Pokémon’s cry is very loud and distracting',
    detail:
      'This Pokémon’s cry is very loud and distracting and more and more and more',
    link: 'https://www.google.com'
  },
  {
    title: 'Free for everyone',
    description: 'The fluid of Smeargle’s tail secretions changes',
    detail: 'The fluid of Smeargle’s tail secretions changes in the intensity',
    link: 'https://www.google.com',
    children: (
      <>
        <Text>abc</Text>
        <Image
          mx="auto"
          src="https://images.unsplash.com/photo-1511216335778-7cb8f49fa7a3?ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=720&q=80"
          alt="Random image"
        />
        <Text>
          Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
          nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat,
          sed diam voluptua. At vero eos et accusam et justo duo dolores et ea
          rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem
          ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur
          sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et
          dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam
          et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea
          takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit
          amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor
          invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.
          At vero eos et accusam et justo duo dolores et ea rebum. Stet clita
          kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit
          amet. Duis autem vel eum iriure dolor in hendrerit in vulputate velit
          esse molestie consequat, vel illum dolore eu feugiat nulla facilisis
          at vero eros et accumsan et iusto odio dignissim qui blandit praesent
          luptatum zzril delenit augue duis dolore the feugait nulla facilisi.
          Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam
          nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat
          volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation
          ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat.
          Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse
          molestie consequat, vel illum dolore eu feugiat nulla facilisis at
          vero eros et accumsan et iusto odio dignissim qui blandit praesent
          luptatum zzril delenit augue duis dolore the feugait nulla facilisi.
          Name liber tempor cum soluta nobis eleifend option congue nihil
          imperdiet doming id quod mazim placerat facer possim assume. Lorem
          ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy
          nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat.
          Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper
          suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem
          vel eum iriure dolor in hendrerit in vulputate velit esse molestie
          consequat, vel illum dolore eu feugiat nulla facilisis. At vero eos et
          accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren,
          no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum
          dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod
          tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
          voluptua. At vero eos et accusam et justo duo dolores et ea rebum.
          Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
          dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing
          elitr, At accusam aliquyam diam diam dolore dolores duo eirmod eos
          erat, et nonumy sed tempor et et invidunt justo labore Stet clita ea
          et gubergren, kasd magna no rebum. sanctus sea sed takimata ut vero
          voluptua. est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet,
          consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut
          labore et dolore magna aliquyam erat. Consetetur sadipscing elitr, sed
          diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam
          erat, sed diam voluptua. At vero eos et accusam et justo duo dolores
          et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est
          Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur
          sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et
          dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam
          et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea
          takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor
        </Text>
      </>
    )
  },
  {
    title: 'Documentation',
    description: 'Yanma is capable of seeing 360 degrees without'
  },
  {
    title: 'Security',
    description: 'The shell’s rounded shape and the grooves on its.'
  },
  {
    title: 'Analytics',
    description: 'This Pokémon uses its flying ability to quickly chase'
  },
  {
    title: 'Notifications',
    description: 'Combusken battles with the intensely hot flames it spews'
  }
];

export const emptyServerAPI = {
  server: null,
  version: null,
  instance: null,
  apiVersion: null,
  worker_running: null,
  worker_pending_tasks: null,
  plugins_enabled: null,
  active_plugins: []
};

export interface SiteMarkProps {
  value: number;
  label: MantineSize;
}

export const SizeMarks: SiteMarkProps[] = [
  { value: 0, label: 'xs' },
  { value: 25, label: 'sm' },
  { value: 50, label: 'md' },
  { value: 75, label: 'lg' },
  { value: 100, label: 'xl' }
];
