/**
 * Interface which defines a single plugin object
 */
export interface PluginInterface {
  pk: number;
  key: string;
  name: string;
  active: boolean;
  is_builtin: boolean;
  is_sample: boolean;
  is_installed: boolean;
  is_package: boolean;
  package_name: string | null;
  admin_js_file: string | null;
  meta: {
    author: string | null;
    description: string | null;
    human_name: string | null;
    license: string | null;
    package_path: string | null;
    pub_date: string | null;
    settings_url: string | null;
    slug: string | null;
    version: string | null;
    website: string | null;
  };
  mixins: Record<
    string,
    {
      key: string;
      human_name: string;
    }
  >;
}
