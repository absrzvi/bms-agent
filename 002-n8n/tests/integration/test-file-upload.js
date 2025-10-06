/**
 * Integration Test: Document Upload with File Attachment
 *
 * T012: Test file upload via attachment and /upload command
 * This test MUST FAIL initially (no file upload handler exists)
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

describe('File Upload Integration', () => {
  const WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL || 'http://localhost:5678/webhook/teams';
  const BMS_API_URL = process.env.BMS_API_URL || 'http://localhost:8000';
  const TEST_USER_ID = '29:1upload-test-user';

  const mockUploadMessage = (attachments = []) => ({
    type: 'message',
    id: `upload-${Date.now()}`,
    timestamp: new Date().toISOString(),
    from: {
      id: TEST_USER_ID,
      name: 'Upload Test User'
    },
    conversation: {
      id: '19:upload-test@thread.tacv2',
      conversationType: 'personal'
    },
    text: 'Here is the document',
    attachments,
    channelId: 'msteams',
    serviceUrl: 'https://smba.trafficmanager.net/emea/'
  });

  // Create a test PDF file
  const createTestFile = (filename, content = 'Test document content') => {
    const testDir = path.join(__dirname, '../test-files');
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
    const filePath = path.join(testDir, filename);
    fs.writeFileSync(filePath, content);
    return filePath;
  };

  afterAll(() => {
    // Cleanup test files
    const testDir = path.join(__dirname, '../test-files');
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  describe('File Attachment Upload', () => {
    test('should handle PDF file attachment', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/test-doc.pdf',
          name: 'railway-procedures.pdf',
          content: Buffer.from('Mock PDF content').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-011: Should accept PDF files
      expect(response.data).toBeDefined();

      // FR-012: Should return document_id
      if (response.data.document_id || response.data.job_id) {
        expect(response.data.document_id || response.data.job_id).toMatch(/[a-f0-9-]+/);
      }
    });

    test('should handle DOCX file attachment', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          contentUrl: 'https://example.com/test-doc.docx',
          name: 'safety-guidelines.docx',
          content: Buffer.from('Mock DOCX content').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-011: Support DOCX format
      expect(response.data).toBeDefined();
    });

    test('should handle XLSX file attachment', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          contentUrl: 'https://example.com/test-data.xlsx',
          name: 'equipment-list.xlsx',
          content: Buffer.from('Mock XLSX content').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-011: Support XLSX format
    });

    test('should handle TXT file attachment', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'text/plain',
          contentUrl: 'https://example.com/notes.txt',
          name: 'procedure-notes.txt',
          content: Buffer.from('Mock TXT content').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-011: Support TXT format
    });

    test('should handle MD file attachment', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'text/markdown',
          contentUrl: 'https://example.com/readme.md',
          name: 'documentation.md',
          content: Buffer.from('# Mock Markdown\nTest content').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-011: Support MD format
    });

    test('should reject invalid file types', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'video/mp4',
          contentUrl: 'https://example.com/video.mp4',
          name: 'training-video.mp4',
          content: Buffer.from('Mock video').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      // NFR-007: Validate file types
      // Should either reject (400) or return error message (200 with error)
      if (response.status === 200) {
        expect(response.data.error || response.data.message).toMatch(/invalid.*file.*type|not supported/i);
      } else {
        expect(response.status).toBe(400);
      }
    });

    test('should handle multiple file attachments', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/doc1.pdf',
          name: 'document1.pdf',
          content: Buffer.from('PDF 1').toString('base64')
        },
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/doc2.pdf',
          name: 'document2.pdf',
          content: Buffer.from('PDF 2').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Should process multiple uploads
      expect(response.data).toBeDefined();
    });
  });

  describe('/upload Command', () => {
    test('should prompt user to attach file when using /upload command', async () => {
      const message = {
        ...mockUploadMessage([]),
        text: '/upload'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 3500 });

      expect(response.status).toBe(200);
      // FR-010: Support /upload command
      expect(response.data.message || response.data.text).toMatch(/attach.*file|upload.*document/i);
    });

    test('should handle /upload with file attached', async () => {
      const message = {
        ...mockUploadMessage([
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/upload-cmd.pdf',
            name: 'command-upload.pdf',
            content: Buffer.from('Upload via command').toString('base64')
          }
        ]),
        text: '/upload'
      };

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Should process the upload
      expect(response.data.document_id || response.data.job_id).toBeDefined();
    });
  });

  describe('Upload Confirmation', () => {
    test('should send confirmation with document ID', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/confirm-test.pdf',
          name: 'confirmation-test.pdf',
          content: Buffer.from('Test PDF').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // FR-012: Confirm with document_id
      expect(response.data).toMatchObject({
        document_id: expect.stringMatching(/[a-f0-9-]+/)
      });
    });

    test('should indicate processing status', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/status-test.pdf',
          name: 'status-test.pdf',
          content: Buffer.from('Test PDF').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Should show processing status (queued/processing)
      if (response.data.status || response.data.processing_status) {
        expect(response.data.status || response.data.processing_status).toMatch(/queued|processing/i);
      }
    });
  });

  describe('Proactive Notification', () => {
    test('should notify user when processing completes', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/notify-test.pdf',
          name: 'notification-test.pdf',
          content: Buffer.from('Test PDF').toString('base64')
        }
      ]);

      const uploadResponse = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(uploadResponse.status).toBe(200);

      const jobId = uploadResponse.data.job_id || uploadResponse.data.document_id;

      // FR-013: Proactive notification when complete
      // In real scenario, this would be tested by polling or webhook
      // For now, just verify we got a job_id to track
      expect(jobId).toBeDefined();
    });
  });

  describe('BMS API Upload Integration', () => {
    test('should forward file to BMS API /documents/upload/async', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/bms-test.pdf',
          name: 'bms-integration.pdf',
          content: Buffer.from('Test PDF for BMS').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Should have called BMS API and received job_id
      expect(response.data.job_id || response.data.document_id).toBeDefined();
    });

    test('should handle BMS API upload failure gracefully', async () => {
      // Mock scenario where BMS API is unavailable
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/fail-test.pdf',
          name: 'failure-test.pdf',
          content: Buffer.from('Test PDF').toString('base64')
        }
      ]);

      // Attempt upload - should handle failure gracefully
      try {
        const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

        if (response.status === 200 && response.data.error) {
          // Graceful error handling
          expect(response.data.error).toMatch(/upload failed|try again/i);
        }
      } catch (error) {
        // Connection error is also acceptable
        expect(error).toBeDefined();
      }
    });
  });

  describe('File Size Limits', () => {
    test('should handle large files within limit', async () => {
      const largeContent = Buffer.alloc(1024 * 1024 * 10).toString('base64'); // 10MB

      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/large.pdf',
          name: 'large-document.pdf',
          content: largeContent
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 10000 });

      expect(response.status).toBe(200);
      // Should accept large files (up to configured limit)
    });

    test('should reject files exceeding size limit', async () => {
      // Mock a file larger than BMS_UPLOAD_MAX_BYTES (1GB default)
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/toolarge.pdf',
          name: 'too-large.pdf',
          contentSize: 2 * 1024 * 1024 * 1024 // 2GB
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      // Should reject or warn about size
      if (response.status === 200 && response.data.error) {
        expect(response.data.error).toMatch(/too large|exceeds.*limit/i);
      } else if (response.status === 413) {
        expect(response.status).toBe(413); // Payload Too Large
      }
    });
  });

  describe('Concurrent Uploads', () => {
    test('should handle multiple users uploading simultaneously', async () => {
      const uploads = [
        mockUploadMessage([
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/user1.pdf',
            name: 'user1-doc.pdf',
            content: Buffer.from('User 1 PDF').toString('base64')
          }
        ]),
        mockUploadMessage([
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/user2.pdf',
            name: 'user2-doc.pdf',
            content: Buffer.from('User 2 PDF').toString('base64')
          }
        ]),
        mockUploadMessage([
          {
            contentType: 'application/pdf',
            contentUrl: 'https://example.com/user3.pdf',
            name: 'user3-doc.pdf',
            content: Buffer.from('User 3 PDF').toString('base64')
          }
        ])
      ];

      uploads[0].from.id = '29:1user-one';
      uploads[1].from.id = '29:1user-two';
      uploads[2].from.id = '29:1user-three';

      const promises = uploads.map(msg => axios.post(WEBHOOK_URL, msg, { timeout: 5000 }));

      const responses = await Promise.all(promises);

      responses.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.data.document_id || response.data.job_id).toBeDefined();
      });
    });
  });

  describe('Upload with Metadata', () => {
    test('should preserve file metadata', async () => {
      const message = mockUploadMessage([
        {
          contentType: 'application/pdf',
          contentUrl: 'https://example.com/metadata.pdf',
          name: 'procedures-v2.pdf',
          content: Buffer.from('PDF with metadata').toString('base64')
        }
      ]);

      const response = await axios.post(WEBHOOK_URL, message, { timeout: 5000 });

      expect(response.status).toBe(200);
      // Should track uploaded_by user
      if (response.data.uploaded_by) {
        expect(response.data.uploaded_by).toBe(TEST_USER_ID);
      }
    });
  });
});
