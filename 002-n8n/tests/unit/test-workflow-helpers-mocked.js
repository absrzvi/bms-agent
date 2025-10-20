/**
 * Mocked Unit Test: Workflow Helper Functions
 *
 * Tests all utility functions in lib/workflow-helpers.js
 * Uses no external dependencies - pure unit testing
 */

const {
  extractMessageData,
  validateQueryLength,
  parseCommand,
  formatCitations,
  formatSearchResults,
  cosineSimilarity,
  validateFileType,
  parseIntent
} = require('../../lib/workflow-helpers');

describe('Workflow Helpers - extractMessageData', () => {
  test('should extract all fields from complete message', () => {
    const message = {
      id: 'msg-123',
      from: { id: '29:user-456', name: 'Test User' },
      conversation: { id: '19:conv-789' },
      channelData: { channel: { id: 'channel-abc' } },
      text: 'Hello bot',
      attachments: [{ contentType: 'application/pdf' }],
      serviceUrl: 'https://smba.trafficmanager.net/emea/',
      timestamp: '2025-10-10T12:00:00Z'
    };

    const result = extractMessageData(message);

    expect(result).toEqual({
      messageId: 'msg-123',
      fromId: '29:user-456',
      fromName: 'Test User',
      conversationId: '19:conv-789',
      channelId: 'channel-abc',
      text: 'Hello bot',
      attachments: [{ contentType: 'application/pdf' }],
      serviceUrl: 'https://smba.trafficmanager.net/emea/',
      timestamp: '2025-10-10T12:00:00Z'
    });
  });

  test('should handle missing optional fields with defaults', () => {
    const message = {
      id: 'msg-456'
    };

    const result = extractMessageData(message);

    expect(result.messageId).toBe('msg-456');
    expect(result.fromId).toBe('');
    expect(result.fromName).toBe('');
    expect(result.conversationId).toBe('');
    expect(result.channelId).toBe('');
    expect(result.text).toBe('');
    expect(result.attachments).toEqual([]);
    expect(result.serviceUrl).toBe('');
    expect(result.timestamp).toBeDefined();
  });

  test('should fallback to conversation ID when channelData missing', () => {
    const message = {
      id: 'msg-789',
      conversation: { id: '19:fallback-conv' }
    };

    const result = extractMessageData(message);

    expect(result.channelId).toBe('19:fallback-conv');
    expect(result.conversationId).toBe('19:fallback-conv');
  });
});

describe('Workflow Helpers - validateQueryLength', () => {
  test('should allow queries within length limit', () => {
    const result = validateQueryLength('What is the emergency brake procedure?', 1000);

    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('should reject queries exceeding length limit', () => {
    const longQuery = 'a'.repeat(1001);
    const result = validateQueryLength(longQuery, 1000);

    expect(result.valid).toBe(false);
    expect(result.error).toBe('query_too_long');
    expect(result.message).toContain('1000 characters');
  });

  test('should allow empty text', () => {
    const result = validateQueryLength('', 1000);

    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('should allow null text', () => {
    const result = validateQueryLength(null, 1000);

    expect(result.valid).toBe(true);
    expect(result.error).toBeNull();
  });

  test('should use custom max length', () => {
    const result = validateQueryLength('12345', 3);

    expect(result.valid).toBe(false);
    expect(result.message).toContain('3 characters');
  });
});

describe('Workflow Helpers - parseCommand', () => {
  test('should parse valid command with arguments', () => {
    const result = parseCommand('/search emergency brake');

    expect(result.isCommand).toBe(true);
    expect(result.command).toBe('/search');
    expect(result.args).toEqual(['emergency', 'brake']);
    expect(result.fullText).toBe('/search emergency brake');
  });

  test('should parse command without arguments', () => {
    const result = parseCommand('/help');

    expect(result.isCommand).toBe(true);
    expect(result.command).toBe('/help');
    expect(result.args).toEqual([]);
  });

  test('should return false for non-command text', () => {
    const result = parseCommand('This is a normal question');

    expect(result.isCommand).toBe(false);
    expect(result.command).toBeNull();
    expect(result.args).toEqual([]);
  });

  test('should return false for null text', () => {
    const result = parseCommand(null);

    expect(result.isCommand).toBe(false);
    expect(result.command).toBeNull();
  });

  test('should normalize command to lowercase', () => {
    const result = parseCommand('/HELP');

    expect(result.command).toBe('/help');
  });

  test('should handle extra whitespace in command', () => {
    const result = parseCommand('  /search   brake  procedures  ');

    expect(result.isCommand).toBe(true);
    expect(result.command).toBe('/search');
    expect(result.args).toEqual(['brake', 'procedures']);
  });
});

describe('Workflow Helpers - formatCitations', () => {
  test('should format citations with all fields', () => {
    const citations = [
      {
        document_name: 'Safety Manual',
        document_section: 'Section 4.2',
        relevance_score: 0.95
      },
      {
        document_name: 'Operations Guide',
        document_section: 'Chapter 3',
        score: 0.88
      }
    ];

    const result = formatCitations(citations);

    expect(result).toContain('Sources:');
    expect(result).toContain('1. Safety Manual, Section 4.2 (Relevance: 0.95)');
    expect(result).toContain('2. Operations Guide, Chapter 3 (Relevance: 0.88)');
  });

  test('should format citations without document section', () => {
    const citations = [
      {
        document_name: 'Quick Reference',
        relevance_score: 0.75
      }
    ];

    const result = formatCitations(citations);

    expect(result).toContain('1. Quick Reference');
    expect(result).not.toContain('undefined');
  });

  test('should return empty string for null citations', () => {
    const result = formatCitations(null);

    expect(result).toBe('');
  });

  test('should return empty string for empty array', () => {
    const result = formatCitations([]);

    expect(result).toBe('');
  });

  test('should handle missing scores with default 0', () => {
    const citations = [
      { document_name: 'Test Doc' }
    ];

    const result = formatCitations(citations);

    expect(result).toContain('(Relevance: 0.00)');
  });
});

describe('Workflow Helpers - formatSearchResults', () => {
  test('should format search results with content excerpts', () => {
    const results = [
      {
        document_name: 'Brake Manual',
        score: 0.92,
        content: 'Emergency brake procedures require activation within 3 seconds of detecting hazard. The system must respond immediately to ensure passenger safety.'
      }
    ];

    const formatted = formatSearchResults(results);

    expect(formatted).toContain('Found 1 documents:');
    expect(formatted).toContain('1. Brake Manual (Score: 0.92)');
    expect(formatted).toContain('Emergency brake procedures');
  });

  test('should limit results to specified count', () => {
    const results = Array.from({ length: 10 }, (_, i) => ({
      document_name: `Doc ${i + 1}`,
      score: 0.8
    }));

    const formatted = formatSearchResults(results, 3);

    expect(formatted).toContain('Found 10 documents:');
    expect(formatted).toContain('1. Doc 1');
    expect(formatted).toContain('2. Doc 2');
    expect(formatted).toContain('3. Doc 3');
    expect(formatted).not.toContain('4. Doc 4');
    expect(formatted).toContain('... and 7 more results');
  });

  test('should return no results message for empty array', () => {
    const formatted = formatSearchResults([]);

    expect(formatted).toBe('No results found for your query. Try rephrasing or using different keywords.');
  });

  test('should return no results message for null input', () => {
    const formatted = formatSearchResults(null);

    expect(formatted).toBe('No results found for your query. Try rephrasing or using different keywords.');
  });

  test('should truncate long excerpts to 150 characters', () => {
    const longContent = 'a'.repeat(200);
    const results = [
      {
        document_name: 'Long Doc',
        score: 0.85,
        content: longContent
      }
    ];

    const formatted = formatSearchResults(results);

    expect(formatted).toMatch(/a{150}\.\.\./);
  });

  test('should handle excerpt_text field as fallback', () => {
    const results = [
      {
        document_name: 'Test',
        score: 0.7,
        excerpt_text: 'This is excerpt text'
      }
    ];

    const formatted = formatSearchResults(results);

    expect(formatted).toContain('This is excerpt text');
  });
});

describe('Workflow Helpers - cosineSimilarity', () => {
  test('should calculate similarity for identical vectors', () => {
    const vecA = [1, 2, 3];
    const vecB = [1, 2, 3];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBeCloseTo(1.0, 5);
  });

  test('should calculate similarity for orthogonal vectors', () => {
    const vecA = [1, 0, 0];
    const vecB = [0, 1, 0];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBeCloseTo(0.0, 5);
  });

  test('should calculate similarity for opposite vectors', () => {
    const vecA = [1, 2, 3];
    const vecB = [-1, -2, -3];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBeCloseTo(-1.0, 5);
  });

  test('should return 0 for vectors of different lengths', () => {
    const vecA = [1, 2, 3];
    const vecB = [1, 2];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBe(0);
  });

  test('should return 0 for null vectors', () => {
    const result = cosineSimilarity(null, [1, 2, 3]);

    expect(result).toBe(0);
  });

  test('should return 0 for zero-length vectors', () => {
    const vecA = [0, 0, 0];
    const vecB = [1, 2, 3];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBe(0);
  });

  test('should calculate similarity for normalized vectors', () => {
    const vecA = [0.6, 0.8];
    const vecB = [0.8, 0.6];

    const result = cosineSimilarity(vecA, vecB);

    expect(result).toBeGreaterThan(0);
    expect(result).toBeLessThan(1);
  });
});

describe('Workflow Helpers - validateFileType', () => {
  test('should allow valid PDF file', () => {
    const result = validateFileType('document.pdf');

    expect(result.valid).toBe(true);
    expect(result.extension).toBe('.pdf');
  });

  test('should allow all supported file types', () => {
    const validFiles = [
      'doc.pdf', 'data.csv', 'sheet.xlsx', 'old-sheet.xls',
      'note.txt', 'readme.md', 'report.docx', 'slides.pptx'
    ];

    for (const filename of validFiles) {
      const result = validateFileType(filename);
      expect(result.valid).toBe(true);
    }
  });

  test('should reject invalid file types', () => {
    const result = validateFileType('image.png');

    expect(result.valid).toBe(false);
    expect(result.error).toBe('file_type_invalid');
    expect(result.message).toContain('Supported:');
  });

  test('should handle uppercase extensions', () => {
    const result = validateFileType('DOCUMENT.PDF');

    expect(result.valid).toBe(true);
    expect(result.extension).toBe('.pdf');
  });

  test('should reject files with no extension', () => {
    const result = validateFileType('noextension');

    expect(result.valid).toBe(false);
  });

  test('should handle files with multiple dots', () => {
    const result = validateFileType('my.document.final.pdf');

    expect(result.valid).toBe(true);
    expect(result.extension).toBe('.pdf');
  });
});

describe('Workflow Helpers - parseIntent', () => {
  test('should parse ASK intent', () => {
    const result = parseIntent('This is an ASK query');

    expect(result).toBe('ask');
  });

  test('should parse SEARCH intent', () => {
    const result = parseIntent('User wants to SEARCH documents');

    expect(result).toBe('search');
  });

  test('should parse COMMAND intent', () => {
    const result = parseIntent('This is a COMMAND');

    expect(result).toBe('command');
  });

  test('should parse UPLOAD intent', () => {
    const result = parseIntent('User wants to UPLOAD file');

    expect(result).toBe('upload');
  });

  test('should default to ask for unknown intent', () => {
    const result = parseIntent('No clear intent here');

    expect(result).toBe('ask');
  });

  test('should handle null input with default', () => {
    const result = parseIntent(null);

    expect(result).toBe('ask');
  });

  test('should be case-insensitive', () => {
    const result1 = parseIntent('ask the bot');
    const result2 = parseIntent('ASK the bot');
    const result3 = parseIntent('AsK the bot');

    expect(result1).toBe('ask');
    expect(result2).toBe('ask');
    expect(result3).toBe('ask');
  });

  test('should prioritize first matching intent', () => {
    const result = parseIntent('ASK and SEARCH');

    expect(result).toBe('ask');
  });
});
