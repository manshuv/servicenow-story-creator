// ServiceNow Table API client for rm_story
const axios = require('axios');

function normalizeInstanceUrl(raw) {
  if (!raw) throw new Error('Missing ServiceNow instance URL');
  try {
    const u = new URL(raw);
    return `${u.protocol}//${u.host}`;
  } catch (e) {
    // If user passed host only, assume https
    if (raw.includes('.')) return `https://${raw}`;
    throw new Error('Invalid ServiceNow instance URL');
  }
}

function api(base, path) {
  return `${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
}

function headers() {
  return { Accept: 'application/json', 'Content-Type': 'application/json' };
}

async function findExistingStory(client, baseUrl, title) {
  const url = api(baseUrl, '/api/now/table/rm_story');
  const params = { sysparm_query: `short_description=${title}`, sysparm_limit: '1' };
  try {
    const resp = await client.get(url, { params, headers: headers() });
    const result = resp.data?.result || [];
    if (Array.isArray(result) && result.length) return result[0];
  } catch (err) {
    throw new Error(`Failed to search stories: ${err.response?.status} ${err.response?.data ? JSON.stringify(err.response.data) : err.message}`);
  }
  // Try legacy prefix
  const legacy = `User Story: ${title}`;
  const paramsLegacy = { sysparm_query: `short_description=${legacy}`, sysparm_limit: '1' };
  try {
    const resp2 = await client.get(url, { params: paramsLegacy, headers: headers() });
    const result2 = resp2.data?.result || [];
    if (Array.isArray(result2) && result2.length) return result2[0];
  } catch (_) {}
  return null;
}

async function createStory(client, baseUrl, payload) {
  const url = api(baseUrl, '/api/now/table/rm_story');
  const resp = await client.post(url, payload, { headers: headers() });
  return resp.data?.result || {};
}

async function updateStory(client, baseUrl, sysId, payload) {
  const url = api(baseUrl, `/api/now/table/rm_story/${sysId}`);
  const resp = await client.patch(url, payload, { headers: headers() });
  return resp.data?.result || {};
}

function recordUrl(baseUrl, sysId) {
  return `${baseUrl}/nav_to.do?uri=rm_story.do?sys_id=${sysId}`;
}

function buildClient({ username, password }) {
  const auth = { username, password };
  return axios.create({ auth });
}

module.exports = {
  normalizeInstanceUrl,
  findExistingStory,
  createStory,
  updateStory,
  recordUrl,
  buildClient,
};
