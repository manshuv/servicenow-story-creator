// Parser for Markdown user stories
// - Extracts title (H1 or first non-empty line)
// - Extracts Description and Acceptance Criteria sections
// - Converts to HTML by default using markdown-it

const fs = require('fs');

function extractTitle(lines) {
  let title = null;
  let titleLineIdx = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (/^\s*#\s+.+/.test(line)) {
      title = line.replace(/^\s*#\s+/, '').trim();
      titleLineIdx = i;
      break;
    }
  }
  if (title === null) {
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.trim()) {
        title = line.trim();
        titleLineIdx = i;
        break;
      }
    }
  }
  if (title === null) {
    throw new Error('Could not determine a title from the markdown.');
  }
  // Remove leading 'User Story:' prefix if present
  title = title.replace(/^\s*user\s*story:\s*/i, '').trim();
  return { title, titleLineIdx };
}

function parseSections(lines, startIdx) {
  const sections = {};
  let current = null;
  const headerRegex = /^\s*\*\*([^*]+):\*\*\s*$/i;
  for (let i = startIdx; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(headerRegex);
    if (m) {
      current = m[1].trim();
      sections[current] = [];
      continue;
    }
    if (current) {
      sections[current].push(line);
    }
  }
  return sections;
}

function parseMarkdownFile(filePath, { sendAsHtml = true } = {}) {
  const content = fs.readFileSync(filePath, 'utf-8').trim();
  if (!content) throw new Error('Markdown file is empty.');
  const lines = content.split(/\r?\n/);

  const { title, titleLineIdx } = extractTitle(lines);
  const scanStart = titleLineIdx != null ? titleLineIdx + 1 : 0;
  const sections = parseSections(lines, scanStart);

  let description = null;
  let acceptanceCriteria = null;

  // Description priority: explicit Description section, else remainder after title (excluding Acceptance Criteria)
  for (const key of Object.keys(sections)) {
    if (key.toLowerCase() === 'description') {
      description = sections[key].join('\n').trim();
      break;
    }
  }
  for (const key of Object.keys(sections)) {
    if (key.toLowerCase() === 'acceptance criteria') {
      acceptanceCriteria = sections[key].join('\n').trim();
      break;
    }
  }

  if (description == null) {
    let descLines = lines.slice(scanStart);
    if (acceptanceCriteria) {
      const accIdx = descLines.findIndex(l => /^\s*\*\*Acceptance Criteria:\*\*\s*$/i.test(l));
      if (accIdx >= 0) descLines = descLines.slice(0, accIdx);
    }
    description = descLines.join('\n').trim();
  }

  if (sendAsHtml) {
    const md = require('markdown-it')({ html: false, linkify: true, breaks: false });
    description = md.render(description || '');
    if (acceptanceCriteria) acceptanceCriteria = md.render(acceptanceCriteria);
  }

  return { title, description, acceptanceCriteria };
}

module.exports = {
  parseMarkdownFile,
};
