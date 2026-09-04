import type { CodexServerMessage, JsonRpcNotification, JsonRpcRequest, JsonRpcResponse } from './types'
import { invoke } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'

export type TransportState = 'idle' | 'connecting' | 'open' | 'closed' | 'error'

export interface CodexTransport {
  readonly state: TransportState
  connect(options?: { cwd?: string }): Promise<void>
  send(message: JsonRpcRequest | JsonRpcNotification | JsonRpcResponse): void
  close(): void
  onMessage(listener: (message: CodexServerMessage) => void): () => void
  onStateChange(listener: (state: TransportState) => void): () => void
}

type Listener<T> = (value: T) => void

/** Browser-safe transport for an app-server WebSocket listener.
 * Authenticated remote connections should be established by the native shell,
 * because browser WebSocket cannot set the Authorization handshake header.
 */
export class WebSocketTransport implements CodexTransport {
  private socket: WebSocket | null = null
  private currentState: TransportState = 'idle'
  private readonly messageListeners = new Set<Listener<CodexServerMessage>>()
  private readonly stateListeners = new Set<Listener<TransportState>>()

  constructor(private readonly endpoint: string) {}

  get state() { return this.currentState }

  async connect(): Promise<void> {
    if (!this.endpoint) throw new Error('Codex App Server endpoint is not configured')
    this.setState('connecting')
    await new Promise<void>((resolve, reject) => {
      const socket = new WebSocket(this.endpoint)
      this.socket = socket
      socket.addEventListener('open', () => { this.setState('open'); resolve() }, { once: true })
      socket.addEventListener('message', (event) => {
        try { this.messageListeners.forEach((listener) => listener(JSON.parse(String(event.data)))) }
        catch { this.setState('error') }
      })
      socket.addEventListener('error', () => { this.setState('error'); reject(new Error('Unable to connect to Codex App Server')) }, { once: true })
      socket.addEventListener('close', () => this.setState('closed'))
    })
  }

  send(message: JsonRpcRequest | JsonRpcNotification | JsonRpcResponse) {
    if (this.socket?.readyState !== WebSocket.OPEN) throw new Error('Codex App Server transport is not open')
    this.socket.send(JSON.stringify(message))
  }

  close() { this.socket?.close(); this.socket = null; this.setState('closed') }
  onMessage(listener: Listener<CodexServerMessage>) { this.messageListeners.add(listener); return () => this.messageListeners.delete(listener) }
  onStateChange(listener: Listener<TransportState>) { this.stateListeners.add(listener); return () => this.stateListeners.delete(listener) }

  private setState(state: TransportState) { this.currentState = state; this.stateListeners.forEach((listener) => listener(state)) }
}

/** Explicit placeholder for the native stdio/unix adapter to be supplied by Tauri later. */
export class UnavailableTransport implements CodexTransport {
  readonly state: TransportState = 'idle'
  async connect(): Promise<void> { throw new Error('Native Codex transport is not available in the browser shell') }
  send(): void { throw new Error('Native Codex transport is not available in the browser shell') }
  close(): void {}
  onMessage() { return () => undefined }
  onStateChange() { return () => undefined }
}

/** Native Tauri transport for the official `codex app-server --stdio` process. */
export class TauriTransport implements CodexTransport {
  private currentState: TransportState = 'idle'
  private readonly messageListeners = new Set<Listener<CodexServerMessage>>()
  private readonly stateListeners = new Set<Listener<TransportState>>()
  private unlistenMessage: UnlistenFn | undefined
  private unlistenStopped: UnlistenFn | undefined

  get state() { return this.currentState }

  async connect(options?: { cwd?: string }): Promise<void> {
    if (this.currentState === 'open') return
    this.setState('connecting')
    this.unlistenMessage = await listen<string>('app-server-message', (event) => {
      try { const message = JSON.parse(event.payload) as CodexServerMessage; this.messageListeners.forEach((listener) => listener(message)) }
      catch { this.setState('error') }
    })
    this.unlistenStopped = await listen('app-server-stopped', () => this.setState('closed'))
    try { await invoke('app_server_start', { cwd: options?.cwd ?? null }); this.setState('open') }
    catch (error) { this.setState('error'); await this.cleanup(); throw new Error(String(error)) }
  }

  send(message: JsonRpcRequest | JsonRpcNotification | JsonRpcResponse) {
    if (this.currentState !== 'open') throw new Error('Codex App Server transport is not open')
    void invoke('app_server_send', { message: JSON.stringify(message) }).catch(() => this.setState('error'))
  }

  close() { void invoke('app_server_stop').finally(() => { void this.cleanup(); this.setState('closed') }) }
  onMessage(listener: Listener<CodexServerMessage>) { this.messageListeners.add(listener); return () => this.messageListeners.delete(listener) }
  onStateChange(listener: Listener<TransportState>) { this.stateListeners.add(listener); return () => this.stateListeners.delete(listener) }

  private async cleanup() { await this.unlistenMessage?.(); await this.unlistenStopped?.(); this.unlistenMessage = undefined; this.unlistenStopped = undefined }
  private setState(state: TransportState) { this.currentState = state; this.stateListeners.forEach((listener) => listener(state)) }
}
