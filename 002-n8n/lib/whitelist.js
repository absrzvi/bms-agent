/**
 * Whitelist Validation Logic (T025)
 *
 * Purpose: Channel and admin access control for POC phase
 * Used by: main-bot-handler workflow
 * Storage: File-based JSON with 60s in-memory cache
 */

const fs = require('fs');
const path = require('path');

const WHITELIST_PATH = process.env.WHITELIST_PATH || 
  path.join(__dirname, '../config/whitelist.json');

class WhitelistManager {
  constructor() {
    this.cache = null;
    this.lastRefresh = 0;
    this.cacheTTL = 60000; // 60 seconds
  }

  loadWhitelist() {
    const now = Date.now();

    if (this.cache && (now - this.lastRefresh < this.cacheTTL)) {
      console.log('[Whitelist] Using cached data');
      return this.cache;
    }

    try {
      const data = fs.readFileSync(WHITELIST_PATH, 'utf8');
      this.cache = JSON.parse(data);
      this.lastRefresh = now;
      console.log('[Whitelist] Loaded from file');
      return this.cache;
    } catch (error) {
      console.error('[Whitelist] Failed to load:', error.message);
      this.cache = { admins: [], channels: [] };
      return this.cache;
    }
  }

  isChannelAllowed(channelId) {
    const whitelist = this.loadWhitelist();
    return whitelist.channels.some(ch =>
      ch.channel_id === channelId && ch.status === 'active'
    );
  }

  isAdmin(userId) {
    const whitelist = this.loadWhitelist();
    return whitelist.admins.includes(userId);
  }

  addChannel(channelId, channelName, addedBy) {
    try {
      const whitelist = this.loadWhitelist();

      if (!this.isAdmin(addedBy)) {
        return { success: false, message: 'unauthorized_admin' };
      }

      const exists = whitelist.channels.some(ch => ch.channel_id === channelId);
      if (exists) {
        return { success: false, message: 'Channel already whitelisted' };
      }

      const newChannel = {
        whitelist_id: 'wl-' + Date.now(),
        channel_id: channelId,
        channel_name: channelName,
        added_by: addedBy,
        added_at: new Date().toISOString(),
        status: 'active'
      };

      whitelist.channels.push(newChannel);
      fs.writeFileSync(WHITELIST_PATH, JSON.stringify(whitelist, null, 2));
      this.cache = null;

      return { success: true, message: 'whitelist_added', channel: newChannel };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  revokeChannel(channelId, revokedBy) {
    try {
      const whitelist = this.loadWhitelist();

      if (!this.isAdmin(revokedBy)) {
        return { success: false, message: 'unauthorized_admin' };
      }

      const channel = whitelist.channels.find(ch => ch.channel_id === channelId);
      if (!channel) {
        return { success: false, message: 'Channel not found' };
      }

      channel.status = 'revoked';
      fs.writeFileSync(WHITELIST_PATH, JSON.stringify(whitelist, null, 2));
      this.cache = null;

      return { success: true, message: 'whitelist_revoked', channel: channel };
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  listChannels() {
    const whitelist = this.loadWhitelist();
    return whitelist.channels.filter(ch => ch.status === 'active');
  }

  listAdmins() {
    const whitelist = this.loadWhitelist();
    return whitelist.admins;
  }
}

let whitelistInstance = null;

function getWhitelistManager() {
  if (!whitelistInstance) {
    whitelistInstance = new WhitelistManager();
  }
  return whitelistInstance;
}

module.exports = { WhitelistManager, getWhitelistManager };
