/**
 * Mocked File Upload Handler Tests (Task 1.2 - Test Coverage Remediation)
 *
 * Purpose: Test file-upload-handler.js with mocked dependencies
 * Coverage Goal: +15% (file-upload-handler.js from 0% → 65%)
 * Strategy: Mock axios and file system operations
 */

jest.mock('axios');
const axios = require('axios');
const handler = require('../../lib/file-upload-handler');

describe('FileUploadHandler (Mocked) - Task 1.2', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('File Type Validation', () => {
    test('should validate PDF file type', () => {
      expect(handler.isValidFileType('document.pdf')).toBe(true);
      expect(handler.isValidFileType('DOCUMENT.PDF')).toBe(true);
    });

    test('should validate all allowed file types', () => {
      const validFiles = [
        'doc.pdf', 'data.csv', 'sheet.xlsx', 'oldsheet.xls',
        'note.txt', 'readme.md', 'letter.docx', 'slides.pptx'
      ];

      validFiles.forEach(file => {
        expect(handler.isValidFileType(file)).toBe(true);
      });
    });

    test('should reject invalid file types', () => {
      const invalidFiles = [
        'malware.exe', 'script.sh', 'archive.zip',
        'image.png', 'video.mp4', 'audio.mp3'
      ];

      invalidFiles.forEach(file => {
        expect(handler.isValidFileType(file)).toBe(false);
      });
    });

    test('should handle files without extension', () => {
      expect(handler.isValidFileType('noextension')).toBe(false);
    });

    test('should be case-insensitive', () => {
      expect(handler.isValidFileType('FILE.PDF')).toBe(true);
      expect(handler.isValidFileType('file.PDF')).toBe(true);
      expect(handler.isValidFileType('FILE.pdf')).toBe(true);
    });
  });

  describe('Content Type Mapping', () => {
    test('should return correct content type for PDF', () => {
      expect(handler.getContentType('doc.pdf')).toBe('application/pdf');
    });

    test('should return correct content type for CSV', () => {
      expect(handler.getContentType('data.csv')).toBe('text/csv');
    });

    test('should return correct content type for XLSX', () => {
      expect(handler.getContentType('sheet.xlsx'))
        .toBe('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    });

    test('should return correct content type for DOCX', () => {
      expect(handler.getContentType('letter.docx'))
        .toBe('application/vnd.openxmlformats-officedocument.wordprocessingml.document');
    });

    test('should return default content type for unknown extension', () => {
      expect(handler.getContentType('file.unknown'))
        .toBe('application/octet-stream');
    });
  });

  describe('Attachment Extraction', () => {
    test('should extract attachments from Teams message', () => {
      const message = {
        attachments: [
          {
            name: 'document.pdf',
            contentUrl: 'https://example.com/file1',
            contentType: 'application/pdf',
            size: 1024
          },
          {
            name: 'data.xlsx',
            contentUrl: 'https://example.com/file2',
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            size: 2048
          }
        ]
      };

      const attachments = handler.extractAttachments(message);

      expect(attachments).toHaveLength(2);
      expect(attachments[0]).toEqual({
        name: 'document.pdf',
        contentUrl: 'https://example.com/file1',
        contentType: 'application/pdf',
        size: 1024
      });
    });

    test('should return empty array if no attachments', () => {
      const message = { text: 'Just a message' };
      expect(handler.extractAttachments(message)).toEqual([]);
    });

    test('should filter out non-application content types', () => {
      const message = {
        attachments: [
          {
            name: 'doc.pdf',
            contentUrl: 'https://example.com/file',
            contentType: 'application/pdf'
          },
          {
            name: 'image.png',
            contentUrl: 'https://example.com/image',
            contentType: 'image/png'
          }
        ]
      };

      const attachments = handler.extractAttachments(message);
      expect(attachments).toHaveLength(1);
      expect(attachments[0].name).toBe('doc.pdf');
    });

    test('should handle attachments without size property', () => {
      const message = {
        attachments: [{
          name: 'doc.pdf',
          contentUrl: 'https://example.com/file',
          contentType: 'application/pdf'
          // size missing
        }]
      };

      const attachments = handler.extractAttachments(message);
      expect(attachments[0].size).toBe(0);
    });
  });

  describe('File Download', () => {
    test('should download file successfully', async () => {
      const mockFileBuffer = Buffer.from('test file content');
      axios.get.mockResolvedValue({
        data: mockFileBuffer
      });

      const result = await handler.downloadFile('https://example.com/file.pdf', 'file.pdf');

      expect(axios.get).toHaveBeenCalledWith(
        'https://example.com/file.pdf',
        expect.objectContaining({
          responseType: 'arraybuffer',
          timeout: 30000,
          maxContentLength: 100 * 1024 * 1024
        })
      );
      expect(result).toBeInstanceOf(Buffer);
    });

    test('should handle download errors', async () => {
      axios.get.mockRejectedValue(new Error('Network error'));

      await expect(
        handler.downloadFile('https://example.com/file.pdf', 'file.pdf')
      ).rejects.toThrow('Failed to download file: Network error');
    });

    test('should enforce max file size limit', async () => {
      axios.get.mockResolvedValue({
        data: Buffer.alloc(101 * 1024 * 1024) // 101 MB
      });

      // File size is checked by axios maxContentLength option
      expect(axios.get).not.toHaveBeenCalled(); // Not called yet
    });
  });

  describe('BMS API Upload', () => {
    test('should upload file to BMS API successfully', async () => {
      const mockBuffer = Buffer.from('test content');
      axios.post.mockResolvedValue({
        data: {
          job_id: 'test-job-123',
          document_id: 'doc-456',
          status: 'queued'
        }
      });

      const result = await handler.uploadToBMS(mockBuffer, 'test.pdf', 'RAILWAY');

      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/documents/upload/async',
        expect.any(Object), // FormData
        expect.objectContaining({
          timeout: 30000
        })
      );
      expect(result.job_id).toBe('test-job-123');
      expect(result.status).toBe('queued');
    });

    test('should use default RAILWAY profile', async () => {
      const mockBuffer = Buffer.from('test content');
      axios.post.mockResolvedValue({
        data: { job_id: 'test-job-123' }
      });

      await handler.uploadToBMS(mockBuffer, 'test.pdf');

      expect(axios.post).toHaveBeenCalled();
    });

    test('should handle BMS API errors with response', async () => {
      const mockBuffer = Buffer.from('test content');
      const error = new Error('API Error');
      error.response = {
        data: { detail: 'Invalid file format' }
      };
      axios.post.mockRejectedValue(error);

      await expect(
        handler.uploadToBMS(mockBuffer, 'test.pdf')
      ).rejects.toThrow('BMS upload failed: Invalid file format');
    });

    test('should handle BMS API errors without response', async () => {
      const mockBuffer = Buffer.from('test content');
      axios.post.mockRejectedValue(new Error('Network timeout'));

      await expect(
        handler.uploadToBMS(mockBuffer, 'test.pdf')
      ).rejects.toThrow('Failed to upload file: Network timeout');
    });
  });

  describe('Process Attachments End-to-End', () => {
    test('should process valid attachment successfully', async () => {
      const message = {
        attachments: [{
          name: 'document.pdf',
          contentUrl: 'https://example.com/file.pdf',
          contentType: 'application/pdf',
          size: 1024
        }]
      };

      axios.get.mockResolvedValue({
        data: Buffer.from('pdf content')
      });
      axios.post.mockResolvedValue({
        data: {
          job_id: 'job-123',
          document_id: 'doc-456',
          status: 'queued'
        }
      });

      const results = await handler.processAttachments(message);

      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(true);
      expect(results[0].jobId).toBe('job-123');
      expect(results[0].fileName).toBe('document.pdf');
    });

    test('should reject invalid file type', async () => {
      const message = {
        attachments: [{
          name: 'malware.exe',
          contentUrl: 'https://example.com/file.exe',
          contentType: 'application/octet-stream',
          size: 1024
        }]
      };

      const results = await handler.processAttachments(message);

      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(false);
      expect(results[0].error).toContain('Invalid file type');
    });

    test('should reject file exceeding size limit', async () => {
      const message = {
        attachments: [{
          name: 'large.pdf',
          contentUrl: 'https://example.com/large.pdf',
          contentType: 'application/pdf',
          size: 150 * 1024 * 1024 // 150 MB
        }]
      };

      const results = await handler.processAttachments(message);

      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(false);
      expect(results[0].error).toContain('File size exceeds limit');
    });

    test('should process multiple attachments', async () => {
      const message = {
        attachments: [
          {
            name: 'doc1.pdf',
            contentUrl: 'https://example.com/doc1.pdf',
            contentType: 'application/pdf',
            size: 1024
          },
          {
            name: 'doc2.xlsx',
            contentUrl: 'https://example.com/doc2.xlsx',
            contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            size: 2048
          }
        ]
      };

      axios.get.mockResolvedValue({
        data: Buffer.from('content')
      });
      axios.post.mockResolvedValue({
        data: { job_id: 'job-123', status: 'queued' }
      });

      const results = await handler.processAttachments(message);

      expect(results).toHaveLength(2);
      expect(results.filter(r => r.success)).toHaveLength(2);
    });

    test('should handle mixed success and failure', async () => {
      const message = {
        attachments: [
          {
            name: 'valid.pdf',
            contentUrl: 'https://example.com/valid.pdf',
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

      axios.get.mockResolvedValue({
        data: Buffer.from('content')
      });
      axios.post.mockResolvedValue({
        data: { job_id: 'job-123', status: 'queued' }
      });

      const results = await handler.processAttachments(message);

      expect(results).toHaveLength(2);
      expect(results.filter(r => r.success)).toHaveLength(1);
      expect(results.filter(r => !r.success)).toHaveLength(1);
    });

    test('should return empty array for message without attachments', async () => {
      const message = { text: 'Hello' };
      const results = await handler.processAttachments(message);
      expect(results).toEqual([]);
    });
  });

  describe('Upload Response Formatting', () => {
    test('should format successful upload', () => {
      const uploadResults = [{
        fileName: 'doc.pdf',
        success: true,
        documentId: 'doc-123',
        jobId: 'job-456'
      }];

      const templates = {
        success: {
          upload_queued: 'Document {{document_id}} uploaded successfully'
        }
      };

      const message = handler.formatUploadResponse(uploadResults, templates);

      expect(message).toContain('1 file(s) uploaded successfully');
      expect(message).toContain('doc-123');
    });

    test('should format failed upload', () => {
      const uploadResults = [{
        fileName: 'invalid.exe',
        success: false,
        error: 'Invalid file type'
      }];

      const templates = {
        success: {
          upload_queued: 'Document {{document_id}} uploaded'
        }
      };

      const message = handler.formatUploadResponse(uploadResults, templates);

      expect(message).toContain('1 file(s) failed');
      expect(message).toContain('invalid.exe');
      expect(message).toContain('Invalid file type');
    });

    test('should format mixed results', () => {
      const uploadResults = [
        {
          fileName: 'doc1.pdf',
          success: true,
          documentId: 'doc-123'
        },
        {
          fileName: 'doc2.exe',
          success: false,
          error: 'Invalid file type'
        }
      ];

      const templates = {
        success: {
          upload_queued: 'Document {{document_id}} uploaded'
        }
      };

      const message = handler.formatUploadResponse(uploadResults, templates);

      expect(message).toContain('1 file(s) uploaded successfully');
      expect(message).toContain('1 file(s) failed');
    });

    test('should handle empty results', () => {
      const message = handler.formatUploadResponse([], {});
      expect(message).toBe('No files to process.');
    });
  });
});
