export type PluginExtension = 'provider' | 'tool' | 'mcp' | 'skill' | 'panel' | 'workflow'

export interface CatCodexPluginManifest {
  id: string
  name: string
  version: string
  extensions: PluginExtension[]
  entrypoint: string
  permissions: string[]
}

/** The first-stage registry is intentionally empty until a signed plugin is installed. */
export const installedPlugins: CatCodexPluginManifest[] = []

export const extensionLabels: Record<PluginExtension, string> = {
  provider: 'Provider', tool: 'Tools', mcp: 'MCP', skill: 'Skills', panel: 'Panels', workflow: 'Workflows',
}
