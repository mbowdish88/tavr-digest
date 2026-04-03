#!/usr/bin/env python3
"""Paper Sorter Dashboard — local Flask app for triaging inbox papers.

Usage:
    python knowledge/paper_sorter_app.py
    # Opens at http://localhost:8003

Features:
    - Browse inbox papers with metadata (title, journal, key finding, etc.)
    - One-click Verify / Exclude / Skip
    - PDF preview in browser
    - Filter by valve type, journal, year
    - Progress tracking
"""

import json
import os
import re
from pathlib import Path

from flask import Flask, jsonify, request, send_file, render_template_string

app = Flask(__name__)

KNOWLEDGE_DIR = Path(__file__).parent
PAPERS_DIR = KNOWLEDGE_DIR / "papers"
INBOX_DIR = PAPERS_DIR / "inbox"
VERIFIED_DIR = PAPERS_DIR / "verified"
EXCLUDED_DIR = PAPERS_DIR / "excluded"
INDEX_PATH = KNOWLEDGE_DIR / "papers_index.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Sorter — The Valve Wire</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f0;
            color: #2d2d2d;
        }
        .header {
            background: #3d1f2b;
            color: #f5f0eb;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 18px; font-weight: 600; letter-spacing: 1px; }
        .stats {
            display: flex;
            gap: 20px;
            font-size: 13px;
        }
        .stats span { opacity: 0.8; }
        .stats strong { color: #e8c4c4; }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            height: calc(100vh - 60px);
        }
        .paper-list {
            overflow-y: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .filters {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e5e5;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filters select, .filters input {
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }
        .filters input { flex: 1; min-width: 150px; }
        .paper-item {
            padding: 12px 16px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.15s;
        }
        .paper-item:hover { background: #faf8f5; }
        .paper-item.active { background: #f0ebe5; border-left: 3px solid #c4787a; }
        .paper-item .title {
            font-size: 14px;
            font-weight: 500;
            color: #2d2d2d;
            margin-bottom: 4px;
            line-height: 1.3;
        }
        .paper-item .meta {
            font-size: 11px;
            color: #888;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .paper-item .meta .journal {
            color: #3d1f2b;
            font-weight: 600;
        }
        .valve-badge {
            display: inline-block;
            font-size: 10px;
            padding: 1px 6px;
            border-radius: 3px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .valve-aortic { background: #fce4e4; color: #c4787a; }
        .valve-mitral { background: #f0e4f0; color: #8b5e6b; }
        .valve-tricuspid { background: #e4f0f5; color: #4a7b8b; }
        .valve-general { background: #e8e8e8; color: #666; }
        .valve-pulmonic { background: #e4f5e4; color: #3b7b5b; }
        .detail-panel {
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .detail-content {
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }
        .detail-content h2 {
            font-size: 18px;
            color: #2d2d2d;
            margin-bottom: 12px;
            line-height: 1.3;
        }
        .detail-field {
            margin-bottom: 10px;
        }
        .detail-field label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #999;
            display: block;
            margin-bottom: 2px;
        }
        .detail-field .value {
            font-size: 14px;
            color: #333;
            line-height: 1.4;
        }
        .key-finding {
            background: #faf8f5;
            border-left: 3px solid #c4787a;
            padding: 12px 16px;
            margin: 12px 0;
            font-size: 14px;
            line-height: 1.5;
            color: #444;
        }
        .actions {
            padding: 16px 20px;
            border-top: 1px solid #e5e5e5;
            display: flex;
            gap: 10px;
        }
        .btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s;
            letter-spacing: 0.5px;
        }
        .btn:hover { opacity: 0.85; }
        .btn-verify { background: #2d7d46; color: white; }
        .btn-exclude { background: #c44; color: white; }
        .btn-skip { background: #ddd; color: #666; }
        .btn-pdf { background: #3d1f2b; color: white; }
        .empty-state {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #999;
            font-size: 16px;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 100;
        }
        .toast.show { opacity: 1; }
        .toast.verified { background: #2d7d46; }
        .toast.excluded { background: #c44; }
        .keyboard-hint {
            font-size: 11px;
            color: #aaa;
            text-align: center;
            padding: 8px;
            border-top: 1px solid #f0f0f0;
        }
        .keyboard-hint kbd {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>PAPER SORTER</h1>
        <div class="stats">
            <span>Inbox: <strong id="inbox-count">0</strong></span>
            <span>Verified: <strong id="verified-count">0</strong></span>
            <span>Excluded: <strong id="excluded-count">0</strong></span>
        </div>
    </div>
    <div class="container">
        <div class="paper-list">
            <div class="filters">
                <input type="text" id="search" placeholder="Search titles...">
                <select id="valve-filter">
                    <option value="">All valves</option>
                    <option value="aortic">Aortic</option>
                    <option value="mitral">Mitral</option>
                    <option value="tricuspid">Tricuspid</option>
                    <option value="general">General</option>
                </select>
                <select id="journal-filter">
                    <option value="">All journals</option>
                </select>
                <select id="design-filter">
                    <option value="">All designs</option>
                </select>
            </div>
            <div id="papers"></div>
            <div class="keyboard-hint">
                <kbd>V</kbd> Verify &nbsp; <kbd>E</kbd> Exclude &nbsp; <kbd>S</kbd> Skip &nbsp;
                <kbd>P</kbd> PDF &nbsp; <kbd>↑↓</kbd> Navigate
            </div>
        </div>
        <div class="detail-panel">
            <div class="detail-content" id="detail">
                <div class="empty-state">Select a paper to review</div>
            </div>
            <div class="actions" id="actions" style="display:none;">
                <button class="btn btn-verify" onclick="sortPaper('verify')">Verify (V)</button>
                <button class="btn btn-exclude" onclick="sortPaper('exclude')">Exclude (E)</button>
                <button class="btn btn-skip" onclick="nextPaper()">Skip (S)</button>
                <button class="btn btn-pdf" onclick="openPdf()">View PDF (P)</button>
            </div>
        </div>
    </div>
    <div class="toast" id="toast"></div>

    <script>
        let papers = [];
        let filtered = [];
        let currentIdx = -1;
        let currentPaper = null;

        async function loadPapers() {
            const resp = await fetch('/api/papers');
            const data = await resp.json();
            papers = data.papers;
            document.getElementById('inbox-count').textContent = data.counts.inbox;
            document.getElementById('verified-count').textContent = data.counts.verified;
            document.getElementById('excluded-count').textContent = data.counts.excluded;

            // Populate filter dropdowns
            const journals = [...new Set(papers.map(p => p.journal))].sort();
            const jf = document.getElementById('journal-filter');
            journals.forEach(j => {
                const opt = document.createElement('option');
                opt.value = j; opt.textContent = j;
                jf.appendChild(opt);
            });
            const designs = [...new Set(papers.map(p => p.study_design))].sort();
            const df = document.getElementById('design-filter');
            designs.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d; opt.textContent = d;
                df.appendChild(opt);
            });

            applyFilters();
        }

        function applyFilters() {
            const search = document.getElementById('search').value.toLowerCase();
            const valve = document.getElementById('valve-filter').value;
            const journal = document.getElementById('journal-filter').value;
            const design = document.getElementById('design-filter').value;

            filtered = papers.filter(p => {
                if (search && !(p.title || '').toLowerCase().includes(search) &&
                    !(p.key_finding || '').toLowerCase().includes(search)) return false;
                const vt = String(p.valve_type || '');
                if (valve && !vt.includes(valve)) return false;
                if (journal && p.journal !== journal) return false;
                if (design && p.study_design !== design) return false;
                return true;
            });

            renderList();
        }

        function renderList() {
            const container = document.getElementById('papers');
            container.innerHTML = filtered.map((p, i) => {
                const vt = String(p.valve_type || 'general');
                const valveClass = vt.includes('aortic') ? 'aortic' :
                    vt.includes('mitral') ? 'mitral' :
                    vt.includes('tricuspid') ? 'tricuspid' :
                    vt.includes('pulmonic') ? 'pulmonic' : 'general';
                return `<div class="paper-item ${i === currentIdx ? 'active' : ''}" onclick="selectPaper(${i})">
                    <div class="title">${p.title || p.filename}</div>
                    <div class="meta">
                        <span class="journal">${p.journal || '?'}</span>
                        <span>${p.year || '?'}</span>
                        <span class="valve-badge valve-${valveClass}">${valveClass}</span>
                        ${p.trial_name ? '<span>Trial: ' + p.trial_name + '</span>' : ''}
                    </div>
                </div>`;
            }).join('');
        }

        function selectPaper(idx) {
            currentIdx = idx;
            currentPaper = filtered[idx];
            renderList();

            const p = currentPaper;
            const vt = String(p.valve_type || 'general');
            document.getElementById('detail').innerHTML = `
                <h2>${p.title || 'Unknown'}</h2>
                <div class="detail-field">
                    <label>Journal</label>
                    <div class="value">${p.journal || '?'} (${p.year || '?'})</div>
                </div>
                <div class="detail-field">
                    <label>Authors</label>
                    <div class="value">${p.authors || '?'}</div>
                </div>
                <div class="detail-field">
                    <label>Study Design</label>
                    <div class="value">${p.study_design || '?'}</div>
                </div>
                <div class="detail-field">
                    <label>Valve Type</label>
                    <div class="value">${vt}</div>
                </div>
                ${p.trial_name ? `<div class="detail-field">
                    <label>Trial</label>
                    <div class="value">${p.trial_name}</div>
                </div>` : ''}
                ${p.sample_size ? `<div class="detail-field">
                    <label>Sample Size</label>
                    <div class="value">${p.sample_size.toLocaleString()}</div>
                </div>` : ''}
                <div class="detail-field">
                    <label>Key Finding</label>
                    <div class="key-finding">${p.key_finding || 'No finding extracted'}</div>
                </div>
                ${p.clinical_implications ? `<div class="detail-field">
                    <label>Clinical Implications</label>
                    <div class="value">${p.clinical_implications}</div>
                </div>` : ''}
                <div class="detail-field">
                    <label>File</label>
                    <div class="value" style="font-size:12px;color:#999;">${p.filename}</div>
                </div>
            `;
            document.getElementById('actions').style.display = 'flex';
        }

        async function sortPaper(action) {
            if (!currentPaper) return;
            const resp = await fetch('/api/sort', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename: currentPaper.filename, action: action})
            });
            const data = await resp.json();
            if (data.ok) {
                showToast(action === 'verify' ? 'Verified' : 'Excluded',
                          action === 'verify' ? 'verified' : 'excluded');
                // Remove from list and select next
                papers = papers.filter(p => p.filename !== currentPaper.filename);
                applyFilters();
                document.getElementById('inbox-count').textContent = data.counts.inbox;
                document.getElementById('verified-count').textContent = data.counts.verified;
                document.getElementById('excluded-count').textContent = data.counts.excluded;
                if (currentIdx >= filtered.length) currentIdx = filtered.length - 1;
                if (filtered.length > 0) selectPaper(currentIdx);
                else {
                    document.getElementById('detail').innerHTML = '<div class="empty-state">All done!</div>';
                    document.getElementById('actions').style.display = 'none';
                }
            }
        }

        function nextPaper() {
            if (currentIdx < filtered.length - 1) {
                selectPaper(currentIdx + 1);
            }
        }

        function openPdf() {
            if (currentPaper) {
                window.open('/api/pdf/' + encodeURIComponent(currentPaper.filename), '_blank');
            }
        }

        function showToast(msg, cls) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast show ' + cls;
            setTimeout(() => t.className = 'toast', 1500);
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
            switch(e.key.toLowerCase()) {
                case 'v': sortPaper('verify'); break;
                case 'e': sortPaper('exclude'); break;
                case 's': nextPaper(); break;
                case 'p': openPdf(); break;
                case 'arrowdown':
                    e.preventDefault();
                    if (currentIdx < filtered.length - 1) selectPaper(currentIdx + 1);
                    break;
                case 'arrowup':
                    e.preventDefault();
                    if (currentIdx > 0) selectPaper(currentIdx - 1);
                    break;
            }
        });

        // Filter listeners
        document.getElementById('search').addEventListener('input', applyFilters);
        document.getElementById('valve-filter').addEventListener('change', applyFilters);
        document.getElementById('journal-filter').addEventListener('change', applyFilters);
        document.getElementById('design-filter').addEventListener('change', applyFilters);

        loadPapers();
    </script>
</body>
</html>
"""


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def get_counts():
    return {
        "inbox": len(list(INBOX_DIR.glob("*.pdf"))) if INBOX_DIR.exists() else 0,
        "verified": len(list(VERIFIED_DIR.glob("*.pdf"))) if VERIFIED_DIR.exists() else 0,
        "excluded": len(list(EXCLUDED_DIR.glob("*.pdf"))) if EXCLUDED_DIR.exists() else 0,
    }


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/papers")
def api_papers():
    index = load_index()
    inbox_files = set(p.name for p in INBOX_DIR.glob("*.pdf")) if INBOX_DIR.exists() else set()

    # Only show papers that are in inbox
    papers = []
    for p in index:
        fname = p.get("filename", "")
        orig = p.get("original_filename", "")
        if fname in inbox_files or orig in inbox_files:
            papers.append(p)

    # Also show unindexed PDFs
    indexed_files = set(p.get("filename", "") for p in papers) | set(p.get("original_filename", "") for p in papers)
    for pdf in sorted(inbox_files - indexed_files):
        papers.append({"filename": pdf, "title": pdf, "journal": "Not indexed", "valve_type": "unknown"})

    return jsonify({"papers": papers, "counts": get_counts()})


@app.route("/api/sort", methods=["POST"])
def api_sort():
    data = request.json
    filename = data.get("filename", "")
    action = data.get("action", "")

    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    EXCLUDED_DIR.mkdir(parents=True, exist_ok=True)

    # Find the file in inbox
    src = INBOX_DIR / filename
    if not src.exists():
        # Try original filename from index
        for pdf in INBOX_DIR.glob("*.pdf"):
            if pdf.name == filename:
                src = pdf
                break

    if not src.exists():
        return jsonify({"ok": False, "error": "File not found"})

    if action == "verify":
        dest = VERIFIED_DIR / src.name
        src.rename(dest)
    elif action == "exclude":
        dest = EXCLUDED_DIR / src.name
        src.rename(dest)

    return jsonify({"ok": True, "counts": get_counts()})


@app.route("/api/pdf/<path:filename>")
def api_pdf(filename):
    # Check inbox, verified, excluded
    for d in [INBOX_DIR, VERIFIED_DIR, EXCLUDED_DIR, PAPERS_DIR]:
        path = d / filename
        if path.exists():
            return send_file(str(path), mimetype="application/pdf")
    return "Not found", 404


if __name__ == "__main__":
    print("Paper Sorter running at http://localhost:8003")
    app.run(host="0.0.0.0", port=8003, debug=False)
