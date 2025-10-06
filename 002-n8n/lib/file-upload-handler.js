/**
 * File Upload Handler
 * Processes file attachments from MS Teams messages
 * Validates file types and uploads to BMS API
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class FileUploadHandler {
  constructor() {
    this.bmsApiUrl = process.env.BMS_API_URL || 'http://localhost:8000';
    this.allowedExtensions = [
      '.pdf', '.csv', '.xlsx', '.xls', '.txt', '.md', '.docx', '.pptx'
    ];
    this.maxFileSizeBytes = 100 * 1024 * 1024; // 100 MB
  }

  /**
   * Validate file type
   * @param {string} fileName - File name
   * @returns {boolean} Is valid
   */
  isValidFileType(fileName) {
    const ext = path.extname(fileName).toLowerCase();
    return this.allowedExtensions.includes(ext);
  }

  /**
   * Extract attachments from Teams message
   * @param {object} message - Teams message object
   * @returns {array} Array of attachment objects
   */
  extractAttachments(message) {
    if (!message.attachments || message.attachments.length === 0) {
      return [];
    }

    return message.attachments
      .filter(att => att.contentType && att.contentType.startsWith('application/'))
      .map(att => ({
        name: att.name,
        contentUrl: att.contentUrl,
        contentType: att.contentType,
        size: att.size || 0
      }));
  }

  /**
   * Download file from Teams attachment URL
   * @param {string} contentUrl - Attachment content URL
   * @param {string} fileName - File name
   * @returns {Promise<Buffer>} File buffer
   */
  async downloadFile(contentUrl, fileName) {
    try {
      const response = await axios.get(contentUrl, {
        responseType: 'arraybuffer',
        timeout: 30000,
        maxContentLength: this.maxFileSizeBytes
      });

      return Buffer.from(response.data);
    } catch (error) {
      console.error(`Error downloading file ${fileName}:`, error.message);
      throw new Error(`Failed to download file: ${error.message}`);
    }
  }

  /**
   * Upload file to BMS API
   * @param {Buffer} fileBuffer - File buffer
   * @param {string} fileName - File name
   * @param {string} profile - Processing profile (RAILWAY, TECHNICAL, GENERAL)
   * @returns {Promise<object>} Upload response with document_id
   */
  async uploadToBMS(fileBuffer, fileName, profile = 'RAILWAY') {
    try {
      const FormData = require('form-data');
      const form = new FormData();

      form.append('file', fileBuffer, {
        filename: fileName,
        contentType: this.getContentType(fileName)
      });
      form.append('profile', profile);

      const response = await axios.post(
        `${this.bmsApiUrl}/api/v1/documents/upload/async`,
        form,
        {
          headers: form.getHeaders(),
          timeout: 30000
        }
      );

      return response.data;
    } catch (error) {
      console.error(`Error uploading file ${fileName} to BMS:`, error.message);

      if (error.response) {
        throw new Error(`BMS upload failed: ${error.response.data?.detail || error.message}`);
      }

      throw new Error(`Failed to upload file: ${error.message}`);
    }
  }

  /**
   * Process file upload from Teams message
   * @param {object} message - Teams message with attachments
   * @returns {Promise<array>} Array of upload results
   */
  async processAttachments(message) {
    const attachments = this.extractAttachments(message);

    if (attachments.length === 0) {
      return [];
    }

    const results = [];

    for (const attachment of attachments) {
      try {
        // Validate file type
        if (!this.isValidFileType(attachment.name)) {
          results.push({
            fileName: attachment.name,
            success: false,
            error: 'Invalid file type. Supported formats: PDF, CSV, XLSX, XLS, TXT, MD, DOCX, PPTX'
          });
          continue;
        }

        // Validate file size
        if (attachment.size && attachment.size > this.maxFileSizeBytes) {
          results.push({
            fileName: attachment.name,
            success: false,
            error: `File size exceeds limit (max: ${this.maxFileSizeBytes / 1024 / 1024} MB)`
          });
          continue;
        }

        // Download file
        console.log(`Downloading file: ${attachment.name}`);
        const fileBuffer = await this.downloadFile(attachment.contentUrl, attachment.name);

        // Upload to BMS
        console.log(`Uploading file to BMS: ${attachment.name}`);
        const uploadResponse = await this.uploadToBMS(fileBuffer, attachment.name);

        results.push({
          fileName: attachment.name,
          success: true,
          documentId: uploadResponse.document_id || uploadResponse.job_id,
          jobId: uploadResponse.job_id,
          status: uploadResponse.status || 'queued'
        });

      } catch (error) {
        results.push({
          fileName: attachment.name,
          success: false,
          error: error.message
        });
      }
    }

    return results;
  }

  /**
   * Format upload response message
   * @param {array} uploadResults - Array of upload results
   * @param {object} templates - Response templates
   * @returns {string} Formatted message
   */
  formatUploadResponse(uploadResults, templates) {
    if (uploadResults.length === 0) {
      return 'No files to process.';
    }

    let message = '';

    const successful = uploadResults.filter(r => r.success);
    const failed = uploadResults.filter(r => !r.success);

    if (successful.length > 0) {
      message += `✓ ${successful.length} file(s) uploaded successfully:\n\n`;

      successful.forEach(result => {
        const docId = result.documentId || result.jobId;
        message += templates.success.upload_queued
          .replace('{{document_id}}', docId)
          .replace('{{document_id}}', docId) + '\n\n';
      });
    }

    if (failed.length > 0) {
      message += `\n❌ ${failed.length} file(s) failed:\n\n`;

      failed.forEach(result => {
        message += `• ${result.fileName}: ${result.error}\n`;
      });
    }

    return message;
  }

  /**
   * Get content type from file name
   * @param {string} fileName - File name
   * @returns {string} Content type
   */
  getContentType(fileName) {
    const ext = path.extname(fileName).toLowerCase();
    const types = {
      '.pdf': 'application/pdf',
      '.csv': 'text/csv',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.xls': 'application/vnd.ms-excel',
      '.txt': 'text/plain',
      '.md': 'text/markdown',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    };

    return types[ext] || 'application/octet-stream';
  }
}

// Export singleton instance
module.exports = new FileUploadHandler();
