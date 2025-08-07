// Windsurf plugin entry (Node)
// Exposes an executePublishStory function that a Windsurf host can call with settings/secrets/inputs.
// It reuses parser and ServiceNow API client logic.

const path = require('path');
const { parseMarkdownFile } = require('./parser');
const {
  normalizeInstanceUrl,
  findExistingStory,
  createStory,
  updateStory,
  recordUrl,
  buildClient,
} = require('./servicenow');

/**
 * Execute the publish command
 * @param {{
 *  settings: { sn_instance: string, auth_method?: string, send_as_html?: boolean },
 *  secrets: { sn_username?: string, sn_password?: string },
 *  notify?: (msg: string, opts?: { type?: 'info'|'success'|'error', url?: string }) => void,
 * }} context
 * @param {{ filePath: string, updateIfExists?: boolean }} inputs
 */
async function executePublishStory(context, inputs) {
  const notify = context.notify || (() => {});
  const settings = context.settings || {};
  const secrets = context.secrets || {};

  if (!inputs?.filePath) throw new Error('filePath is required');
  const filePath = path.resolve(inputs.filePath);

  const instance = normalizeInstanceUrl(settings.sn_instance || process.env.SN_INSTANCE);
  const username = secrets.sn_username || process.env.SN_USERNAME;
  const password = secrets.sn_password || process.env.SN_PASSWORD;
  if (!instance || !username || !password) {
    throw new Error('Missing instance/username/password in settings/secrets');
  }

  const sendAsHtml = settings.send_as_html !== false; // default true

  // Parse markdown
  const { title, description, acceptanceCriteria } = parseMarkdownFile(filePath, { sendAsHtml });

  // Build payload
  const payload = {
    short_description: title.slice(0, 160),
    description,
  };
  if (acceptanceCriteria) payload.acceptance_criteria = acceptanceCriteria;

  const client = buildClient({ username, password });
  const existing = await findExistingStory(client, instance, title);

  let result;
  if (existing && (inputs.updateIfExists ?? true)) {
    result = await updateStory(client, instance, existing.sys_id, payload);
    notify(`Updated story ${result.number || ''}`, { type: 'success', url: recordUrl(instance, result.sys_id || existing.sys_id) });
  } else if (existing) {
    notify(`Story already exists (${existing.number}). Re-run with updateIfExists to update.`, { type: 'info', url: recordUrl(instance, existing.sys_id) });
    return { existing: true, sys_id: existing.sys_id, url: recordUrl(instance, existing.sys_id) };
  } else {
    result = await createStory(client, instance, payload);
    notify(`Created story ${result.number || ''}`, { type: 'success', url: recordUrl(instance, result.sys_id) });
  }

  return {
    sys_id: (result && result.sys_id) || (existing && existing.sys_id),
    number: (result && result.number) || (existing && existing.number),
    url: recordUrl(instance, (result && result.sys_id) || (existing && existing.sys_id)),
  };
}

module.exports = { executePublishStory };

// Optional local test runner (node windsuite/index.js /path/to/file.md)
if (require.main === module) {
  (async () => {
    const [, , fileArg] = process.argv;
    if (!fileArg) {
      console.error('Usage: node windsuite/index.js <markdown_file>');
      process.exit(1);
    }
    try {
      const res = await executePublishStory({
        settings: { sn_instance: process.env.SN_INSTANCE, send_as_html: true },
        secrets: { sn_username: process.env.SN_USERNAME, sn_password: process.env.SN_PASSWORD },
        notify: (m, o) => console.log(m, o?.url ? `=> ${o.url}` : ''),
      }, { filePath: fileArg, updateIfExists: true });
      console.log('Done:', res);
    } catch (e) {
      console.error('Error:', e.message);
      process.exit(1);
    }
  })();
}
