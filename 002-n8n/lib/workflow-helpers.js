/**
 * Workflow Helper Functions
 * Common utilities for n8n Function nodes
 */

function extractMessageData(message) {
  return {
    messageId: message.id || '',
    fromId: message.from?.id || '',
    fromName: message.from?.name || '',
    conversationId: message.conversation?.id || '',
    channelId: message.channelData?.channel?.id || message.conversation?.id || '',
    text: message.text || '',
    attachments: message.attachments || [],
    serviceUrl: message.serviceUrl || '',
    timestamp: message.timestamp || new Date().toISOString()
  };
}

function validateQueryLength(text, maxLength = 1000) {
  if (!text) return { valid: true, error: null };
  
  if (text.length > maxLength) {
    return {
      valid: false,
      error: 'query_too_long',
      message: 'Query too long. Please limit to ' + maxLength + ' characters.'
    };
  }
  
  return { valid: true, error: null };
}

function parseCommand(text) {
  if (!text || !text.startsWith('/')) {
    return { isCommand: false, command: null, args: [] };
  }
  
  const parts = text.trim().split(/\s+/);
  return {
    isCommand: true,
    command: parts[0].toLowerCase(),
    args: parts.slice(1),
    fullText: text
  };
}

function formatCitations(citations) {
  if (!citations || citations.length === 0) return '';
  
  let formatted = '\n\nSources:\n';
  citations.forEach((cit, idx) => {
    const score = (cit.relevance_score || cit.score || 0).toFixed(2);
    formatted += (idx + 1) + '. ' + cit.document_name;
    if (cit.document_section) {
      formatted += ', ' + cit.document_section;
    }
    formatted += ' (Relevance: ' + score + ')\n';
  });
  
  return formatted;
}

function formatSearchResults(results, limit = 5) {
  if (!results || results.length === 0) {
    return 'No results found for your query. Try rephrasing or using different keywords.';
  }
  
  let formatted = 'Found ' + results.length + ' documents:\n\n';
  const displayResults = results.slice(0, limit);
  
  displayResults.forEach((result, idx) => {
    const score = (result.score || result.relevance_score || 0).toFixed(2);
    formatted += (idx + 1) + '. ' + (result.document_name || 'Unknown') + ' (Score: ' + score + ')\n';
    
    if (result.content || result.excerpt_text) {
      const excerpt = (result.content || result.excerpt_text).substring(0, 150);
      formatted += '   "' + excerpt + (excerpt.length >= 150 ? '...' : '') + '"\n\n';
    }
  });
  
  if (results.length > limit) {
    formatted += '\n... and ' + (results.length - limit) + ' more results';
  }
  
  return formatted;
}

function cosineSimilarity(vecA, vecB) {
  if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  
  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);
  
  return (normA === 0 || normB === 0) ? 0 : dotProduct / (normA * normB);
}

function validateFileType(filename) {
  const allowedExtensions = ['.pdf', '.csv', '.xlsx', '.xls', '.txt', '.md', '.docx', '.pptx'];
  const extension = filename.substring(filename.lastIndexOf('.')).toLowerCase();
  
  if (!allowedExtensions.includes(extension)) {
    return {
      valid: false,
      error: 'file_type_invalid',
      message: 'Invalid file type. Supported: ' + allowedExtensions.join(', ')
    };
  }
  
  return { valid: true, extension };
}

function parseIntent(llmResponse) {
  const response = (llmResponse || '').toUpperCase();
  
  if (response.includes('ASK')) return 'ask';
  if (response.includes('SEARCH')) return 'search';
  if (response.includes('COMMAND')) return 'command';
  if (response.includes('UPLOAD')) return 'upload';
  
  return 'ask'; // Default
}

module.exports = {
  extractMessageData,
  validateQueryLength,
  parseCommand,
  formatCitations,
  formatSearchResults,
  cosineSimilarity,
  validateFileType,
  parseIntent
};
