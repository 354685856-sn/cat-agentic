/**
 * Stable wire primitives from the Codex App Server documentation.
 * The server omits the JSON-RPC 2.0 header on the wire, but request/response
 * shapes still follow JSON-RPC 2.0.
 */
export interface JsonRpcRequest<TParams = unknown> {
  method: string
  id: number
  params: TParams
}

export interface JsonRpcServerRequest<TParams = unknown> {
  method: string
  id: number
  params: TParams
}

export interface JsonRpcNotification<TParams = unknown> {
  method: string
  params: TParams
}

export interface JsonRpcResponse<TResult = unknown> {
  id: number
  result?: TResult
  error?: { code: number; message: string; data?: unknown }
}

export interface ClientInfo {
  name: string
  title: string
  version: string
}

export interface InitializeParams {
  clientInfo: ClientInfo
  capabilities?: {
    experimentalApi?: boolean
    optOutNotificationMethods?: string[]
    requestAttestation?: boolean
    mcpServerOpenaiFormElicitation?: boolean
  }
}

export interface ThreadStartParams {
  model?: string
  cwd?: string
}

export interface TextInput {
  type: 'text'
  text: string
}

export interface TurnStartParams {
  threadId: string
  input: TextInput[]
  model?: string
  cwd?: string
}

export interface ThreadRef { id: string }
export interface ThreadStartResult { thread: ThreadRef }
export interface ThreadResumeParams { threadId: string; cwd?: string; model?: string }

export interface TurnStartedParams { turn: { id: string } }
export interface AgentMessageDeltaParams { delta?: string; threadId?: string; turnId?: string }

export type CodexServerMessage = JsonRpcResponse | JsonRpcNotification | JsonRpcServerRequest

export type ApprovalDecision = 'accept' | 'acceptForSession' | 'decline' | 'cancel'

export interface FileChangeApprovalParams {
  itemId: string
  threadId: string
  turnId: string
  reason?: string
  grantRoot?: string
}

export interface CommandApprovalParams {
  itemId: string
  threadId: string
  turnId: string
  command?: string
  cwd?: string
  reason?: string
}

export interface PermissionsApprovalParams {
  threadId: string
  turnId: string
  itemId: string
  permissions: unknown
  reason?: string
}
