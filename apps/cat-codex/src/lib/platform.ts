export type Platform = 'macos' | 'windows' | 'linux' | 'unknown'

export type PermissionMode = 'ask' | 'read-only' | 'full-access'

export interface PermissionProfile {
  mode: PermissionMode
  network: 'off' | 'on-request' | 'enabled'
  cwd?: string
}

export interface AppServerEndpoint {
  transport: 'stdio' | 'websocket' | 'unix-socket'
  address?: string
  /** Native shells own bearer headers and secret storage; the web UI never receives raw tokens. */
  auth: 'native-managed' | 'none'
}

export interface PlatformAdapter {
  platform: Platform
  pathSeparator: '/' | '\\'
  appServer: AppServerEndpoint
  permissions: PermissionProfile
}

export const defaultPlatformAdapter: PlatformAdapter = {
  platform: 'unknown',
  pathSeparator: '/',
  appServer: { transport: 'stdio', auth: 'native-managed' },
  permissions: { mode: 'ask', network: 'off' },
}
