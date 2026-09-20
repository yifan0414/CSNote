"use strict";

const { Plugin, MarkdownView, Notice, getAllTags } = require("obsidian");

const CAPTURE_FOLDER = "02-Capture/灵感与工具/";
const PAPER_FOLDER = "Paper/";
const LEGACY_STATUS = { inbox: "unread", processed: "read", archive: "archived" };
const SKIP_UPDATE = Symbol("capture-read-status:skip-update");

function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

module.exports = class CaptureReadStatusPlugin extends Plugin {
  onload() {
    this.running = true;
    this.pending = new Set();

    // Register after layout restoration. Enabling the plugin must not mark all
    // previously open tabs as read, and hover previews must not count as opens.
    this.app.workspace.onLayoutReady(() => {
      if (!this.running) return;
      this.registerEvent(
        this.app.workspace.on("file-open", (file) => {
          void this.onFileOpen(file);
        })
      );
    });

    this.addCommand({
      id: "mark-current-note-inbox",
      name: "将当前笔记标记为未读",
      checkCallback: (checking) => {
        const file = this.app.workspace.getActiveFile();
        if (!this.isManagedNote(file) || this.statusOf(file) !== "read") return false;
        if (!checking) void this.updateStatus(file, "read", "unread");
        return true;
      },
    });
  }

  onunload() {
    this.running = false;
  }

  isManagedNote(file, frontmatter) {
    if (!file || file.extension !== "md") return false;
    if (file.path.startsWith(CAPTURE_FOLDER)) return true;
    if (!file.path.startsWith(PAPER_FOLDER)) return false;
    const cache = this.app.metadataCache.getFileCache(file);
    if (!cache) return false;
    // Mirror Papers.base: Paper folder + either paper/arxiv or paper/pdf tag.
    // getAllTags includes YAML tags and inline tags, including nested tags.
    const tags = getAllTags(frontmatter ? { ...cache, frontmatter } : cache) || [];
    return tags.some((tag) => ["#paper/arxiv", "#paper/pdf"].some(
      (prefix) => tag === prefix || tag.startsWith(prefix + "/")
    ));
  }

  statusOf(file, frontmatter = this.app.metadataCache.getFileCache(file)?.frontmatter) {
    if (frontmatter?.status != null) return frontmatter.status;
    // Compatibility with older Capture generators; migrate only on a real update.
    if (file.path.startsWith(CAPTURE_FOLDER)) return LEGACY_STATUS[frontmatter?.["状态"]];
    return undefined;
  }

  async onFileOpen(file) {
    if (!this.running || !this.isManagedNote(file)) return;
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view || view.hoverPopover || view.file?.path !== file.path) return;
    if (this.app.workspace.getActiveFile()?.path !== file.path) return;
    const status = this.statusOf(file);
    if (status !== "unread" && status !== "reading") return;
    await this.updateStatus(file, status, "read");
  }

  async updateStatus(file, from, to) {
    if (!this.running || !this.isManagedNote(file)) return;
    const path = file.path;
    if (this.pending.has(path)) return;
    this.pending.add(path);
    try {
      await this.app.fileManager.processFrontMatter(file, (frontmatter) => {
        // Recheck the current YAML inside the atomic update, since the cache may
        // be stale or the user may have archived/renamed the note in the meantime.
        if (!this.running || !this.isManagedNote(file, frontmatter) || this.statusOf(file, frontmatter) !== from) {
          throw SKIP_UPDATE;
        }
        frontmatter.status = to;
        if (file.path.startsWith(CAPTURE_FOLDER) && Object.hasOwn(LEGACY_STATUS, frontmatter["状态"])) {
          delete frontmatter["状态"];
        }
        frontmatter.updated = localDate();
      });
    } catch (error) {
      if (error !== SKIP_UPDATE) {
        console.error("[Capture & Papers 阅读状态] 无法更新笔记状态", path, error);
        new Notice(`Capture & Papers 阅读状态：未能更新「${file.basename}」，请检查笔记 YAML 或文件是否可写。`);
      }
    } finally {
      this.pending.delete(path);
    }
  }
};
