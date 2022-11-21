import { HostList } from './states';

export const defaultlist: HostList = {
  "https://demo.inventree.org": { host: "https://demo.inventree.org/api/", name: "InvenTree Demo" },
  "https://sample.app.invenhost.com": { host: "https://sample.app.invenhost.com/api/", name: "InvenHost: Sample" },
  "http://localhost:8000": { host: "http://localhost:8000/api/", name: "Localhost" },
};

// Static Settings
export const tabs = [
  { text: "Home", name: "home" },
  { text: "Part", name: "part" },
];

export const links = {
  links: [
    {
      "link": "https://inventree.org/",
      "label": "Website"
    },
    {
      "link": "https://github.com/invenhost/InvenTree",
      "label": "GitHub"
    },
    {
      "link": "https://demo.inventree.org/",
      "label": "Demo"
    }
  ]
};
