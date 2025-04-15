export interface Host {
  host: string;
  name: string;
}

export interface HostList {
  [key: string]: Host;
}
