export interface HealthStatus {
  status: string;
}

export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  conversation_id?: string;
  sequence_order?: number; // Optional, used for ordering messages
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}

export interface SystemPromptItem {
  title: string;
  content: string;
}

export interface SystemPromptSettings {
  system_prompts: SystemPromptItem[];
  include_datetime: boolean;
  enabled: boolean;
  thinking_mode:
    | "default"
    | "</think>"
    | "/no_think"
    | "<no_think>"
    | "<think>"
    | "/think";
}

export interface SamplingSettings {
  temperature: number;
  top_p: number;
  max_tokens: number;
  frequency_penalty: number;
  presence_penalty: number;
  seed?: number;
}

export interface Persona {
  id: string;
  name: string;
  description: string;
  avatar: string;
  isActive: boolean;
  color: string;
}

export interface OpenAISettings {
  base_url: string;
  api_key: string;
  model_name: string;
  streaming_enabled: boolean;
}

export interface ModelInfo {
  id: string;
  created?: number;
  owned_by?: string;
}

export interface ConnectionTestResponse {
  success: boolean;
  message: string;
  model_info?: {
    models: ModelInfo[];
  };
}

export interface ToolInfo {
  id: string;
  name: string;
  description: string;
  module: string;
  enabled: boolean;
  auto_tool?: boolean;
  one_time?: boolean;
  condition?: boolean | null;
  parameters: Record<string, any>;
  ui_feature?: Record<string, any> | null;
}

export interface ToolFeature {
  id: string; // e.g., "private_messages"
  label: string;
  kv_key: string; // e.g., "private_chat"
  icon?: string;
  type?: string; // e.g., "badge_panel", "ui_v1"
  fetch_window?: number;
  source_tool_id?: string;
  sender_name?: string;
  // UI v1 specific fields
  layout?: {
    type: string;
    size?: string;
    title?: string;
    components?: Array<any>;
  };
}

export interface DataSource {
  type: string;
  key?: string;
  endpoint?: string;
  value?: any;
  library_type?: string;
  target_component_id?: string;
  content_source_id?: string;
  include_user?: boolean;
  fetch_window?: number;
}
