/**
 * Typing Indicator Handler
 * Sends typing indicator to MS Teams while bot processes requests
 * Implements FR-016 requirement
 */

const axios = require('axios');

class TypingIndicatorHandler {
  constructor() {
    this.indicatorDuration = 3000; // 3 seconds per indicator
    this.activeIndicators = new Map();
  }

  /**
   * Send typing indicator to Teams
   * @param {string} serviceUrl - Teams service URL
   * @param {string} conversationId - Conversation ID
   * @param {string} botId - Bot application ID
   * @returns {Promise<boolean>} Success
   */
  async sendTypingIndicator(serviceUrl, conversationId, botId) {
    try {
      const endpoint = `${serviceUrl}/v3/conversations/${conversationId}/activities`;

      const activity = {
        type: 'typing',
        from: {
          id: botId,
          name: 'BMS Teams Bot'
        }
      };

      await axios.post(endpoint, activity, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 5000
      });

      return true;
    } catch (error) {
      console.error('Error sending typing indicator:', error.message);
      return false;
    }
  }

  /**
   * Start continuous typing indicator
   * Sends typing indicator every 3 seconds until stopped
   * @param {string} serviceUrl - Teams service URL
   * @param {string} conversationId - Conversation ID
   * @param {string} botId - Bot application ID
   * @returns {string} Indicator ID
   */
  startTypingIndicator(serviceUrl, conversationId, botId) {
    const indicatorId = `${conversationId}-${Date.now()}`;

    // Send first indicator immediately
    this.sendTypingIndicator(serviceUrl, conversationId, botId);

    // Set up interval to send indicator every 3 seconds
    const interval = setInterval(async () => {
      await this.sendTypingIndicator(serviceUrl, conversationId, botId);
    }, this.indicatorDuration);

    // Store interval reference
    this.activeIndicators.set(indicatorId, interval);

    console.log(`Started typing indicator: ${indicatorId}`);
    return indicatorId;
  }

  /**
   * Stop typing indicator
   * @param {string} indicatorId - Indicator ID returned from startTypingIndicator
   */
  stopTypingIndicator(indicatorId) {
    const interval = this.activeIndicators.get(indicatorId);

    if (interval) {
      clearInterval(interval);
      this.activeIndicators.delete(indicatorId);
      console.log(`Stopped typing indicator: ${indicatorId}`);
    }
  }

  /**
   * Send single typing indicator (for short operations)
   * @param {string} serviceUrl - Teams service URL
   * @param {string} conversationId - Conversation ID
   * @param {string} botId - Bot application ID
   * @returns {Promise<boolean>} Success
   */
  async sendSingleIndicator(serviceUrl, conversationId, botId) {
    return await this.sendTypingIndicator(serviceUrl, conversationId, botId);
  }

  /**
   * Wrap async operation with typing indicator
   * Automatically starts and stops indicator around operation
   * @param {string} serviceUrl - Teams service URL
   * @param {string} conversationId - Conversation ID
   * @param {string} botId - Bot application ID
   * @param {Function} operation - Async function to execute
   * @returns {Promise<any>} Operation result
   */
  async withTypingIndicator(serviceUrl, conversationId, botId, operation) {
    const indicatorId = this.startTypingIndicator(serviceUrl, conversationId, botId);

    try {
      const result = await operation();
      return result;
    } finally {
      this.stopTypingIndicator(indicatorId);
    }
  }

  /**
   * Clean up all active indicators
   */
  cleanup() {
    this.activeIndicators.forEach((interval, indicatorId) => {
      this.stopTypingIndicator(indicatorId);
    });
  }

  /**
   * Get count of active indicators
   * @returns {number} Count
   */
  getActiveCount() {
    return this.activeIndicators.size;
  }
}

// Export singleton instance
module.exports = new TypingIndicatorHandler();
