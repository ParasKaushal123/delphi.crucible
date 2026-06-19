"use client";

interface ChatMessage {
  agent: string;
  content: string;
}

interface DebateRingProps {
  bullMessages: ChatMessage[];
  bearMessages: ChatMessage[];
  status: "idle" | "active" | "complete" | "waiting";
  statusText: string;
}

function formatContent(content: string) {
  const parts = content.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part.split("\n").map((line, j) => (
      <span key={`${i}-${j}`}>
        {line}
        {j < part.split("\n").length - 1 && <br />}
      </span>
    ));
  });
}

export default function DebateRing({
  bullMessages,
  bearMessages,
  status,
  statusText,
}: DebateRingProps) {
  return (
    <div className="room-panel debate-ring">
      <div className="room-panel-header">
        <div className="room-panel-title">
          <span className="room-icon">⚔️</span>
          <span className="eyebrow-label">Debate Ring</span>
        </div>
        <div className="room-panel-status">
          <span className={`status-indicator ${status}`} />
          {statusText}
        </div>
      </div>

      <div className="debate-split">
        {/* Bull Side */}
        <div className="debate-side bull">
          <div className="debate-side-header">
            🟢 Bull Case
          </div>
          <div className="room-messages" id="room-debate-bull">
            {bullMessages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🟢</div>
                <div className="empty-state-text">Waiting for @bull-agent...</div>
              </div>
            ) : (
              bullMessages.map((msg, i) => (
                <div className="chat-message" key={i}>
                  <div className="chat-avatar bull">🟢</div>
                  <div className="chat-body">
                    <div className="chat-agent-name bull">@bull-agent</div>
                    <div className="chat-content">{formatContent(msg.content)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Bear Side */}
        <div className="debate-side bear">
          <div className="debate-side-header">
            🔴 Bear Case
          </div>
          <div className="room-messages" id="room-debate-bear">
            {bearMessages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔴</div>
                <div className="empty-state-text">Waiting for @bear-agent...</div>
              </div>
            ) : (
              bearMessages.map((msg, i) => (
                <div className="chat-message" key={i}>
                  <div className="chat-avatar bear">🔴</div>
                  <div className="chat-body">
                    <div className="chat-agent-name bear">@bear-agent</div>
                    <div className="chat-content">{formatContent(msg.content)}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
