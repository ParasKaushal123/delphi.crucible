"use client";

interface ChatMessage {
  agent: string;
  content: string;
  timestamp?: string;
}

interface RoomPanelProps {
  roomName: string;
  roomIcon: string;
  roomClass: string;
  messages: ChatMessage[];
  status: "idle" | "active" | "complete" | "waiting";
  statusText: string;
}

const AGENT_CONFIG: Record<string, { emoji: string; class: string; label: string }> = {
  "pm-agent": { emoji: "🧠", class: "pm", label: "@pm-agent" },
  "quant-agent": { emoji: "📊", class: "quant", label: "@quant-agent" },
  "bull-agent": { emoji: "🟢", class: "bull", label: "@bull-agent" },
  "bear-agent": { emoji: "🔴", class: "bear", label: "@bear-agent" },
  user: { emoji: "👤", class: "user", label: "You" },
};

function formatMessageContent(content: string) {
  // Simple markdown-lite rendering for chat messages
  // Handle **bold** and `code`
  const parts = content.split(/(```[\s\S]*?```|\*\*.*?\*\*|`[^`]+`)/g);

  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const code = part.slice(3, -3).replace(/^[a-z]+\n/, ""); // remove language hint
      return (
        <pre key={i}>
          <code>{code}</code>
        </pre>
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    // Handle line breaks
    return part.split("\n").map((line, j) => (
      <span key={`${i}-${j}`}>
        {line}
        {j < part.split("\n").length - 1 && <br />}
      </span>
    ));
  });
}

export default function RoomPanel({
  roomName,
  roomIcon,
  roomClass,
  messages,
  status,
  statusText,
}: RoomPanelProps) {
  return (
    <div className={`room-panel ${roomClass}`}>
      <div className="room-panel-header">
        <div className="room-panel-title">
          <span className="room-icon">{roomIcon}</span>
          {roomName}
        </div>
        <div className="room-panel-status">
          <span className={`status-indicator ${status}`} />
          {statusText}
        </div>
      </div>

      <div className="room-messages" id={`room-${roomClass}`}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">{roomIcon}</div>
            <div className="empty-state-text">
              Waiting for agents to join this room...
            </div>
          </div>
        ) : (
          messages.map((msg, i) => {
            const agent = AGENT_CONFIG[msg.agent] || AGENT_CONFIG.user;
            return (
              <div className="chat-message" key={i}>
                <div className={`chat-avatar ${agent.class}`}>{agent.emoji}</div>
                <div className="chat-body">
                  <div className={`chat-agent-name ${agent.class}`}>
                    {agent.label}
                  </div>
                  <div className="chat-content">
                    {formatMessageContent(msg.content)}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
