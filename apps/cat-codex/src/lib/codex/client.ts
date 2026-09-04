import type { CodexTransport, TransportState } from './transport'
import type { CodexServerMessage, InitializeParams, JsonRpcResponse, JsonRpcServerRequest, ThreadStartParams, ThreadStartResult, TurnStartParams } from './types'

export type ClientState = 'disconnected' | 'connecting' | 'ready' | 'error'

export class CodexAppServerClient {
  private requestId = 0
  private readonly pending = new Map<number, { resolve: (value: unknown) => void; reject: (reason: Error) => void }>()
  private unsubscribeMessage: (() => void) | undefined
  private unsubscribeTransport: (() => void) | undefined
  private stateValue: ClientState = 'disconnected'
  private readonly stateListeners = new Set<(state: ClientState) => void>()
  private readonly eventListeners = new Set<(message: CodexServerMessage) => void>()
  private readonly requestListeners = new Set<(message: JsonRpcServerRequest) => void>()

  constructor(private readonly transport: CodexTransport) {
    this.unsubscribeMessage = transport.onMessage((message) => this.handleMessage(message))
    this.unsubscribeTransport = transport.onStateChange((state) => this.handleTransportState(state))
  }

  get state() { return this.stateValue }

  async initialize(clientInfo: InitializeParams['clientInfo'], options?: { cwd?: string }) {
    await this.transport.connect(options)
    await this.request('initialize', { clientInfo })
    this.notify('initialized', {})
    this.setState('ready')
  }

  startThread(params: ThreadStartParams = {}) { return this.request<ThreadStartResult>('thread/start', params) }
  startTurn(params: TurnStartParams) { return this.request('turn/start', params) }

  subscribe(listener: (message: CodexServerMessage) => void) { this.eventListeners.add(listener); return () => this.eventListeners.delete(listener) }
  onServerRequest(listener: (message: JsonRpcServerRequest) => void) { this.requestListeners.add(listener); return () => this.requestListeners.delete(listener) }
  respond(id: number, result: unknown) { this.transport.send({ id, result }) }
  dispose() { this.unsubscribeMessage?.(); this.unsubscribeTransport?.(); this.transport.close() }

  private request<TResult = unknown>(method: string, params: unknown): Promise<TResult> {
    const id = ++this.requestId
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve: resolve as (value: unknown) => void, reject })
      try { this.transport.send({ method, id, params }) }
      catch (error) { this.pending.delete(id); reject(error instanceof Error ? error : new Error(String(error))) }
    })
  }

  private notify(method: string, params: unknown) { this.transport.send({ method, params }) }

  private handleMessage(message: CodexServerMessage) {
    if ('method' in message && 'id' in message) {
      this.requestListeners.forEach((listener) => listener(message))
      return
    }
    if ('id' in message) {
      const response = message as JsonRpcResponse
      const pending = this.pending.get(response.id)
      if (!pending) return
      this.pending.delete(response.id)
      if (response.error) pending.reject(new Error(response.error.message))
      else pending.resolve(response.result)
    }
    this.eventListeners.forEach((listener) => listener(message))
  }

  private handleTransportState(state: TransportState) {
    if (state === 'connecting') this.setState('connecting')
    if (state === 'error') this.setState('error')
    if (state === 'closed') this.setState('disconnected')
  }

  private setState(state: ClientState) { this.stateValue = state; this.stateListeners.forEach((listener) => listener(state)) }
  onStateChange(listener: (state: ClientState) => void) { this.stateListeners.add(listener); return () => this.stateListeners.delete(listener) }
}
