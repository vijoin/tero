import { Agent } from "~/utils/agent"

export enum TabDisplayMode {
  FULL = "full",
  MINIMIZED = "minimized",
  CLOSED = "closed"
}

export class TabState {
  sidebarSize: number
  displayMode: TabDisplayMode
  agent?: Agent
  messages: ChatMessage[]

  constructor(sidebarSize: number, displayMode: TabDisplayMode, messages: ChatMessage[], agent?: Agent) {
    this.sidebarSize = sidebarSize
    this.displayMode = displayMode
    this.agent = agent
    this.messages = messages
  }

  public static fromJsonObject(obj: any): TabState {
    return new TabState(obj.sidebarSize, obj.displayMode, obj.messages.map((m: any) => ChatMessage.fromJsonObject(m)), obj.agent ? Agent.fromJsonObject(obj.agent) : undefined)
  }
}

export class ChatMessage {
  id?: number
  text: string
  isUser: boolean
  isComplete: boolean
  isSuccess: boolean

  constructor(text: string, isUser: boolean, isComplete: boolean, isSuccess: boolean, id?: number) {
    this.text = text
    this.isUser = isUser
    this.isComplete = isComplete
    this.isSuccess = isSuccess
    this.id = id
  }

  public static userMessage(text: string): ChatMessage {
    return new ChatMessage(text, true, true, true)
  }

  public static agentMessage(text?: string): ChatMessage {
    return new ChatMessage(text || '', false, text !== undefined, true)
  }

  public static agentErrorMessage(text: string): ChatMessage {
    return new ChatMessage(text || '', false, true, false)
  }

  public static fromJsonObject(obj: any): ChatMessage {
    return new ChatMessage(obj.text, obj.isUser, obj.isComplete, obj.isSuccess, obj.id)
  }
}
