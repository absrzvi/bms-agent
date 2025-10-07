/**
 * Mocked File Upload Handler Tests (Task 1.2 - Coverage Remediation)
 *
 * Purpose: Test file-upload-handler.js with mocked file system and HTTP requests
 * Strategy: Mock axios for HTTP, use real FileUploadHandler logic
 * Coverage Target: +15% (file-upload-handler.js from 0% → 65%)
 */

const axios = require('axios');
const MockAdapter = require('axios-mock-adapter');
const handler = require('../../lib/file-upload-handler');

describe('FileUploadHandler (Mocked) - Task 1.2', () => {
  let mockAxios;

  beforeEach(() => {
    mockAxios = new MockAdapter(axios);
  });

  afterEach(() => {
    mockAxios.restore();
  });

  // ===== File Type Validation Tests =====

  test('should validate PDF file type', () => {
    expect(handler.isValidFileType('document.pdf')).toBe(true);
    expect(handler.isValidFileType('document.PDF')).toBe(true); // Case insensitive
  });

  test('should validate all allowed file types', () => {
    const validFiles = [
      'file.pdf', 'file.csv', 'file.xlsx', 'file.xls',
      'file.txt', 'file.md', 'file.docx', 'file.pptx'
    ];

    validFiles.forEach(file => {
      expect(handler.isValidFileType(file)).toBe(true);
    });
  });

  test('should reject invalid file types', () => {
    const invalidFiles = [
      'malware.exe', 'script.sh', 'archive.zip', 'image.jpg',
      'video.mp4', 'audio.mp3', 'code.js', 'binary.bin'
    ];

    invalidFiles.forEach(file => {
      expect(handler.isValidFileType(file)).toBe(false);
    });
  });

  test('should handle file names without extension', () => {
    expect(handler.isValidFileType('noextension')).toBe(false);
  });

  test('should handle empty file name', () => {
    expect(handler.isValidFileType('')).toBe(false);
  });

  // ===== Attachment Extraction Tests =====

  test('should extract attachments from Teams message', () => {
    const message = {
      attachments: [
        {
          name: 'document.pdf',
          contentUrl: 'https://example.com/document.pdf',
          contentType: 'application/pdf',
          size: 1024
        },
        {
          name: 'spreadsheet.xlsx',
          contentUrl: 'https://example.com/spreadsheet.xlsx',
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          size: 2048
        }
      ]
    };

    const attachments = handler.extractAttachments(message);

    expect(attachments).toHaveLength(2);
    expect(attachments[0].name).toBe('document.pdf');
    expect(attachments[0].contentUrl).toBe('https://example.com/document.pdf');
    expect(attachments[1].name).toBe('spreadsheet.xlsx');
  });

  test('should return empty array if no attachments', () => {
    const message = { text: 'Hello' };
    const attachments = handler.extractAttachments(message);
    expect(attachments).toEqual([]);
  });

  test('should filter out non-application attachments', () => {
    const message = {
      attachments: [
        {
          name: 'document.pdf',
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/doc.pdf'
        },
        {
          name: 'image.jpg',
          contentType: 'image/jpeg',
          contentUrl: 'https://example.com/image.jpg'
        }
      ]
    };

    const attachments = handler.extractAttachments(message);

    expect(attachments).toHaveLength(1);
    expect(attachments[0].name).toBe('document.pdf');
  });

  test('should handle missing size field', () => {
    const message = {
      attachments: [
        {
          name: 'document.pdf',
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/doc.pdf'
          // size not provided
        }
      ]
    };

    const attachments = handler.extractAttachments(message);

    expect(attachments[0].size).toBe(0);
  });

  // ===== File Download Tests =====

  test('should download file from contentUrl', async () => {
    const fileContent = Buffer.from('Mock PDF content');
    mockAxios.onGet('https://example.com/document.pdf').reply(200, fileContent);

    const buffer = await handler.downloadFile('https://example.com/document.pdf', 'document.pdf');

    expect(buffer).toBeInstanceOf(Buffer);
    expect(buffer.toString()).toBe('Mock PDF content');
  });

  test('should handle download errors', async () => {
    mockAxios.onGet('https://example.com/document.pdf').reply(404, 'Not Found');

    await expect(
      handler.downloadFile('https://example.com/document.pdf', 'document.pdf')
    ).rejects.toThrow('Failed to download file');
  });

  test('should respect max file size limit during download', async () => {
    const largeFile = Buffer.alloc(150 * 1024 * 1024); // 150 MB > 100 MB limit
    mockAxios.onGet('https://example.com/large.pdf').reply(200, largeFile);

    // Axios will reject due to maxContentLength
    await expect(
      handler.downloadFile('https://example.com/large.pdf', 'large.pdf')
    ).rejects.toThrow();
  });

  test('should handle network timeout', async () => {
    mockAxios.onGet('https://example.com/document.pdf').timeout();

    await expect(
      handler.downloadFile('https://example.com/document.pdf', 'document.pdf')
    ).rejects.toThrow('Failed to download file');
  });

  // ===== BMS Upload Tests =====

  test('should upload file to BMS API', async () => {
    const fileBuffer = Buffer.from('Test file content');
    const mockResponse = {
      document_id: 'doc-123',
      job_id: 'job-456',
      status: 'queued'
    };

    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(200, mockResponse);

    const result = await handler.uploadToBMS(fileBuffer, 'test.pdf', 'RAILWAY');

    expect(result.document_id).toBe('doc-123');
    expect(result.job_id).toBe('job-456');
    expect(result.status).toBe('queued');
  });

  test('should use default profile if not specified', async () => {
    const fileBuffer = Buffer.from('Test content');
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(200, {
      job_id: 'job-123', status: 'queued'
    });

    await handler.uploadToBMS(fileBuffer, 'test.pdf');

    // Verify default profile is RAILWAY (checked in FormData)
    const request = mockAxios.history.post[0];
    expect(request.data).toContain('RAILWAY');
  });

  test('should handle BMS API 500 error', async () => {
    const fileBuffer = Buffer.from('Test content');
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(500, {
      detail: 'Internal Server Error'
    });

    await expect(
      handler.uploadToBMS(fileBuffer, 'test.pdf')
    ).rejects.toThrow('BMS upload failed');
  });

  test('should handle BMS API timeout', async () => {
    const fileBuffer = Buffer.from('Test content');
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').timeout();

    await expect(
      handler.uploadToBMS(fileBuffer, 'test.pdf')
    ).rejects.toThrow('Failed to upload file');
  });

  // ===== Process Attachments Integration Tests =====

  test('should process single attachment successfully', async () => {
    const message = {
      attachments: [
        {
          name: 'document.pdf',
          contentUrl: 'https://example.com/document.pdf',
          contentType: 'application/pdf',
          size: 1024
        }
      ]
    };

    const fileContent = Buffer.from('PDF content');
    mockAxios.onGet('https://example.com/document.pdf').reply(200, fileContent);
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(200, {
      job_id: 'job-123',
      document_id: 'doc-123',
      status: 'queued'
    });

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(true);
    expect(results[0].fileName).toBe('document.pdf');
    expect(results[0].jobId).toBe('job-123');
    expect(results[0].documentId).toBe('doc-123');
  });

  test('should reject file with invalid type', async () => {
    const message = {
      attachments: [
        {
          name: 'malware.exe',
          contentUrl: 'https://example.com/malware.exe',
          contentType: 'application/octet-stream',
          size: 1024
        }
      ]
    };

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(false);
    expect(results[0].error).toContain('Invalid file type');
  });

  test('should reject file exceeding size limit', async () => {
    const message = {
      attachments: [
        {
          name: 'huge.pdf',
          contentUrl: 'https://example.com/huge.pdf',
          contentType: 'application/pdf',
          size: 150 * 1024 * 1024 // 150 MB
        }
      ]
    };

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(false);
    expect(results[0].error).toContain('File size exceeds limit');
  });

  test('should process multiple attachments (batch upload)', async () => {
    const message = {
      attachments: [
        {
          name: 'doc1.pdf',
          contentUrl: 'https://example.com/doc1.pdf',
          contentType: 'application/pdf',
          size: 1024
        },
        {
          name: 'doc2.pdf',
          contentUrl: 'https://example.com/doc2.pdf',
          contentType: 'application/pdf',
          size: 2048
        }
      ]
    };

    mockAxios.onGet('https://example.com/doc1.pdf').reply(200, Buffer.from('Content 1'));
    mockAxios.onGet('https://example.com/doc2.pdf').reply(200, Buffer.from('Content 2'));
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(config => {
      return [200, { job_id: 'job-' + Math.random(), document_id: 'doc-' + Math.random(), status: 'queued' }];
    });

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(2);
    expect(results[0].success).toBe(true);
    expect(results[1].success).toBe(true);
    expect(results[0].jobId).toBeTruthy();
    expect(results[1].jobId).toBeTruthy();
  });

  test('should handle partial failure in batch upload', async () => {
    const message = {
      attachments: [
        {
          name: 'doc1.pdf',
          contentUrl: 'https://example.com/doc1.pdf',
          contentType: 'application/pdf',
          size: 1024
        },
        {
          name: 'invalid.exe',
          contentUrl: 'https://example.com/invalid.exe',
          contentType: 'application/octet-stream',
          size: 1024
        }
      ]
    };

    mockAxios.onGet('https://example.com/doc1.pdf').reply(200, Buffer.from('Content'));
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(200, {
      job_id: 'job-1', status: 'queued'
    });

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(2);
    expect(results[0].success).toBe(true);
    expect(results[1].success).toBe(false);
    expect(results[1].error).toContain('Invalid file type');
  });

  test('should handle download error during batch processing', async () => {
    const message = {
      attachments: [
        {
          name: 'doc1.pdf',
          contentUrl: 'https://example.com/doc1.pdf',
          contentType: 'application/pdf',
          size: 1024
        }
      ]
    };

    mockAxios.onGet('https://example.com/doc1.pdf').reply(404, 'Not Found');

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(false);
    expect(results[0].error).toContain('Failed to download file');
  });

  test('should handle BMS upload error during batch processing', async () => {
    const message = {
      attachments: [
        {
          name: 'doc1.pdf',
          contentUrl: 'https://example.com/doc1.pdf',
          contentType: 'application/pdf',
          size: 1024
        }
      ]
    };

    mockAxios.onGet('https://example.com/doc1.pdf').reply(200, Buffer.from('Content'));
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(500, {
      detail: 'Processing failed'
    });

    const results = await handler.processAttachments(message);

    expect(results).toHaveLength(1);
    expect(results[0].success).toBe(false);
    expect(results[0].error).toContain('BMS upload failed');
  });

  // ===== Edge Cases =====

  test('should handle empty attachments array', async () => {
    const message = { attachments: [] };
    const results = await handler.processAttachments(message);
    expect(results).toEqual([]);
  });

  test('should handle missing contentType in attachment', () => {
    const message = {
      attachments: [
        {
          name: 'document.pdf',
          contentUrl: 'https://example.com/doc.pdf'
          // contentType missing
        }
      ]
    };

    const attachments = handler.extractAttachments(message);
    expect(attachments).toEqual([]);
  });

  test('should handle BMS API returning job_id without document_id', async () => {
    const message = {
      attachments: [
        {
          name: 'doc.pdf',
          contentUrl: 'https://example.com/doc.pdf',
          contentType: 'application/pdf',
          size: 1024
        }
      ]
    };

    mockAxios.onGet('https://example.com/doc.pdf').reply(200, Buffer.from('Content'));
    mockAxios.onPost('http://localhost:8000/api/v1/documents/upload/async').reply(200, {
      job_id: 'job-123'
      // document_id not included (async upload)
    });

    const results = await handler.processAttachments(message);

    expect(results[0].success).toBe(true);
    expect(results[0].documentId).toBe('job-123'); // Falls back to job_id
  });
});
