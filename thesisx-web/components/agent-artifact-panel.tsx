"use client";

import type { AgentArtifact } from "../lib/types";

export function AgentArtifactPanel({
  artifact,
  acceptLabel = "接受结果",
  rejectLabel = "拒绝结果",
  onAccept,
  onReject,
  onPrimaryAction,
  primaryActionLabel,
}: {
  artifact: AgentArtifact;
  acceptLabel?: string;
  rejectLabel?: string;
  onAccept?: () => void;
  onReject?: () => void;
  onPrimaryAction?: () => void;
  primaryActionLabel?: string;
}) {
  return (
    <div className="stack tight">
      <p className="body-copy">{artifact.summary}</p>
      {artifact.sections.length ? (
        <div className="stack tight">
          {artifact.sections.map((section) => (
            <div key={section.id} className="detail-stack">
              <span className="muted-label">{section.title}</span>
              {section.kind === "markdown" ? (
                <pre className="code-block">{section.content}</pre>
              ) : (
                <p className="body-copy">{section.content}</p>
              )}
            </div>
          ))}
        </div>
      ) : null}
      {artifact.steps.length ? (
        <ul className="entity-list">
          {artifact.steps.map((step) => (
            <li key={step.id}>
              <div>
                <strong>{step.title}</strong>
                <p>{step.rationale}</p>
              </div>
              <span className="badge">{step.target_surface}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {artifact.actions.length ? (
        <div className="detail-stack">
          <span className="muted-label">Suggested Actions</span>
          <ul className="entity-list">
            {artifact.actions.map((action) => (
              <li key={action.id}>
                <div>
                  <strong>{action.label}</strong>
                  <p>{action.intent}</p>
                </div>
                <span className="badge">{action.target_surface}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {!artifact.sections.some((section) => section.kind === "markdown") && artifact.markdown ? (
        <pre className="code-block">{artifact.markdown}</pre>
      ) : null}
      {(onPrimaryAction || onAccept || onReject) ? (
        <div className="panel-actions">
          {onPrimaryAction && primaryActionLabel ? (
            <button className="primary-button" onClick={onPrimaryAction} type="button">
              {primaryActionLabel}
            </button>
          ) : null}
          {onAccept ? (
            <button className="secondary-button" onClick={onAccept} type="button">
              {acceptLabel}
            </button>
          ) : null}
          {onReject ? (
            <button className="secondary-button" onClick={onReject} type="button">
              {rejectLabel}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
