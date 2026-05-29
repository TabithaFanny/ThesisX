"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";

import { getApiHealth, getSettingsStatus, importZotero, scanObsidian } from "../lib/api";
import type { ApiHealth, KnowledgeItem, SettingsStatus } from "../lib/types";
import { ErrorState, Panel, StatCard } from "./ui";

export function SettingsWorkspace() {
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [obsidianPath, setObsidianPath] = useState("");
  const [maxFiles, setMaxFiles] = useState(50);
  const [zoteroPath, setZoteroPath] = useState("");
  const [zoteroFormat, setZoteroFormat] = useState<"bibtex" | "ris">("bibtex");
  const [importedItems, setImportedItems] = useState<KnowledgeItem[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [settingsStatus, apiHealth] = await Promise.all([
          getSettingsStatus(),
          getApiHealth(),
        ]);
        if (!active) {
          return;
        }
        setStatus(settingsStatus);
        setHealth(apiHealth);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "无法读取系统状态。");
        }
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  function onScanObsidian(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    startTransition(async () => {
      try {
        const items = await scanObsidian(obsidianPath, maxFiles);
        setImportedItems(items);
        setMessage(`Obsidian 扫描完成，共得到 ${items.length} 条知识对象。`);
      } catch (scanError) {
        setError(scanError instanceof Error ? scanError.message : "Obsidian 扫描失败。");
      }
    });
  }

  function onImportZotero(event: FormEvent) {
    event.preventDefault();
    setMessage("");
    startTransition(async () => {
      try {
        const items = await importZotero(zoteroPath, zoteroFormat);
        setImportedItems(items);
        setMessage(`Zotero 导入完成，共得到 ${items.length} 条知识对象。`);
      } catch (importError) {
        setError(importError instanceof Error ? importError.message : "Zotero 导入失败。");
      }
    });
  }

  return (
    <div className="stack">
      <div className="stats-grid">
        <StatCard label="数据库" value={status?.db_exists ? "已发现" : "未发现"} />
        <StatCard label="运行目录" value={status?.runs_dir_exists ? "已发现" : "未发现"} />
        <StatCard label="API 状态" value={health?.status || "未知"} />
        <StatCard label="版本" value={status?.version || health?.version || "未知"} />
      </div>

      <div className="two-column">
        <Panel title="本地入口" eyebrow="Environment">
          <div className="selector-grid">
            <a className="selector-card active" href="http://127.0.0.1:3000">
              <strong>Web Workspace</strong>
              <p>前端工作台入口，适合日常操作与联调。</p>
            </a>
            <a className="selector-card" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
              <strong>API Docs</strong>
              <p>查看 FastAPI 自动文档，直接调试 REST 端点。</p>
            </a>
            <a className="selector-card" href="http://127.0.0.1:8000/api/health" target="_blank" rel="noreferrer">
              <strong>Health Check</strong>
              <p>快速确认后端存活和版本状态。</p>
            </a>
          </div>
        </Panel>

        <Panel title="Provider 语义" eyebrow="Settings">
          <ul className="detail-list">
            <li>`mock` 模式允许无密钥运行，用于流程预览与前端联调。</li>
            <li>`real` 模式必须提供 `api_key`、`base_url`、`model`。</li>
            <li>当前 Web MVP 不会在 real 失败时偷偷回退到 mock。</li>
            <li>RAG 索引使用本地 SQLite 持久化，不依赖进程内临时缓存。</li>
          </ul>
        </Panel>
      </div>

      <Panel title="当前系统判定" eyebrow="Runtime">
        <div className="detail-grid">
          <div>
            <span className="muted-label">数据库状态</span>
            <p>{status?.db_exists ? "本地数据库已就绪" : "尚未发现本地数据库文件"}</p>
          </div>
          <div>
            <span className="muted-label">运行目录</span>
            <p>{status?.runs_dir_exists ? "运行历史目录可用" : "尚未发现 runs 目录"}</p>
          </div>
          <div>
            <span className="muted-label">API 连通性</span>
            <p>{health?.status === "ok" ? "后端在线，可继续调试前端页面" : "后端状态未知"}</p>
          </div>
          <div>
            <span className="muted-label">当前阶段</span>
            <p>V5.0 Web Workspace MVP</p>
          </div>
        </div>
      </Panel>

      <div className="two-column">
        <Panel title="Obsidian 扫描" eyebrow="Import">
          <form className="compact-form" onSubmit={onScanObsidian}>
            <label className="full-span">
              Vault 路径
              <input value={obsidianPath} onChange={(event) => setObsidianPath(event.target.value)} placeholder="~/Documents/MyVault" />
            </label>
            <label>
              最大文件数
              <input
                type="number"
                min={1}
                max={500}
                value={maxFiles}
                onChange={(event) => setMaxFiles(Number(event.target.value) || 50)}
              />
            </label>
            <button className="primary-button" disabled={isPending || !obsidianPath.trim()} type="submit">
              {isPending ? "扫描中..." : "开始扫描"}
            </button>
          </form>
        </Panel>

        <Panel title="Zotero 导入" eyebrow="Import">
          <form className="compact-form" onSubmit={onImportZotero}>
            <label className="full-span">
              文件路径
              <input value={zoteroPath} onChange={(event) => setZoteroPath(event.target.value)} placeholder="~/Downloads/library.bib" />
            </label>
            <label>
              格式
              <select value={zoteroFormat} onChange={(event) => setZoteroFormat(event.target.value as "bibtex" | "ris")}>
                <option value="bibtex">bibtex</option>
                <option value="ris">ris</option>
              </select>
            </label>
            <button className="primary-button" disabled={isPending || !zoteroPath.trim()} type="submit">
              {isPending ? "导入中..." : "开始导入"}
            </button>
          </form>
        </Panel>
      </div>

      <Panel title="最近导入结果" eyebrow="Preview">
        {message ? <p className="body-copy">{message}</p> : null}
        {importedItems.length ? (
          <ul className="entity-list">
            {importedItems.slice(0, 8).map((item) => (
              <li key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.item_type}</p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="body-copy">这里会显示最近一次扫描或导入得到的知识对象预览。</p>
        )}
      </Panel>
    </div>
  );
}
