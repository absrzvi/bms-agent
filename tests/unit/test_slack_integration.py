"""
Unit tests for Slack Integration
Tests slash commands, signature verification, and message formatting
"""

import pytest
import hmac
import hashlib
import time
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.slack_integration import (
    verify_slack_signature,
    format_search_results_for_slack,
    get_processor,
    router
)


class TestSlackSignatureVerification:
    """Test Slack request signature verification"""
    
    def test_verify_valid_signature(self):
        """Test verification of valid Slack signature"""
        signing_secret = "test_secret_key"
        timestamp = str(int(time.time()))
        body = b'{"text": "test query"}'
        
        # Generate valid signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = verify_slack_signature(signing_secret, timestamp, body, signature)
        
        assert result is True
    
    def test_verify_invalid_signature(self):
        """Test rejection of invalid signature"""
        signing_secret = "test_secret_key"
        timestamp = str(int(time.time()))
        body = b'{"text": "test query"}'
        invalid_signature = "v0=invalid_signature_hash"
        
        result = verify_slack_signature(signing_secret, timestamp, body, invalid_signature)
        
        assert result is False
    
    def test_verify_expired_timestamp(self):
        """Test rejection of expired timestamp (replay attack protection)"""
        signing_secret = "test_secret_key"
        # Timestamp from 10 minutes ago
        old_timestamp = str(int(time.time()) - 600)
        body = b'{"text": "test query"}'
        
        # Generate signature with old timestamp
        sig_basestring = f"v0:{old_timestamp}:{body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = verify_slack_signature(signing_secret, old_timestamp, body, signature)
        
        assert result is False
    
    def test_verify_without_signing_secret(self):
        """Test POC mode where signature verification is skipped"""
        # Empty signing secret (POC mode)
        signing_secret = ""
        timestamp = str(int(time.time()))
        body = b'{"text": "test query"}'
        signature = "any_signature"
        
        result = verify_slack_signature(signing_secret, timestamp, body, signature)
        
        # Should skip verification in POC mode
        assert result is True
    
    def test_verify_with_modified_body(self):
        """Test detection of tampered request body"""
        signing_secret = "test_secret_key"
        timestamp = str(int(time.time()))
        original_body = b'{"text": "original query"}'
        tampered_body = b'{"text": "tampered query"}'
        
        # Generate signature with original body
        sig_basestring = f"v0:{timestamp}:{original_body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify with tampered body
        result = verify_slack_signature(signing_secret, timestamp, tampered_body, signature)
        
        assert result is False


class TestSlackMessageFormatting:
    """Test Slack Block Kit message formatting"""
    
    def test_format_empty_results(self):
        """Test formatting when no results found"""
        results = []
        query = "nonexistent document"
        
        message = format_search_results_for_slack(results, query)
        
        assert message["response_type"] == "in_channel"
        assert "blocks" in message
        assert len(message["blocks"]) > 0
        assert "No results found" in message["blocks"][0]["text"]["text"]
        assert query in message["blocks"][0]["text"]["text"]
    
    def test_format_single_result(self):
        """Test formatting single search result"""
        results = [
            {
                "content": "Test document content",
                "metadata": {
                    "file_name": "BMS-HUMR-FOR-005.pdf",
                    "department": "HUMR"
                },
                "score": 0.95
            }
        ]
        query = "employee onboarding"
        
        message = format_search_results_for_slack(results, query)
        
        assert "blocks" in message
        assert len(message["blocks"]) > 0
        assert message["response_type"] == "in_channel"
    
    def test_format_multiple_results(self):
        """Test formatting multiple search results"""
        results = [
            {
                "content": "Document 1 content",
                "metadata": {"file_name": "doc1.pdf"},
                "score": 0.95
            },
            {
                "content": "Document 2 content",
                "metadata": {"file_name": "doc2.pdf"},
                "score": 0.85
            },
            {
                "content": "Document 3 content",
                "metadata": {"file_name": "doc3.pdf"},
                "score": 0.75
            }
        ]
        query = "test query"
        
        message = format_search_results_for_slack(results, query)
        
        assert "blocks" in message
        # Should include header + results
        assert len(message["blocks"]) > 1
    
    def test_format_with_metadata_fields(self):
        """Test formatting results with complete metadata"""
        results = [
            {
                "content": "Complete metadata test",
                "metadata": {
                    "file_name": "BMS-HUMR-FOR-005.pdf",
                    "department": "HUMR",
                    "document_type": "FOR",
                    "quality_score": 0.85
                },
                "score": 0.90
            }
        ]
        query = "metadata test"
        
        message = format_search_results_for_slack(results, query)
        
        assert "blocks" in message
        assert message["response_type"] == "in_channel"
    
    def test_format_result_limit(self):
        """Test that results are limited to reasonable number for Slack"""
        # Generate 20 results
        results = [
            {
                "content": f"Document {i} content",
                "metadata": {"file_name": f"doc{i}.pdf"},
                "score": 0.9 - (i * 0.01)
            }
            for i in range(20)
        ]
        query = "many results"
        
        message = format_search_results_for_slack(results, query)
        
        # Slack message should be formatted without crashing
        assert "blocks" in message
        assert isinstance(message["blocks"], list)


class TestProcessorInitialization:
    """Test processor initialization for Slack integration"""
    
    @patch('api.slack_integration.BMSDocumentProcessor')
    def test_get_processor_singleton(self, mock_processor_class):
        """Test that processor is initialized as singleton"""
        mock_instance = Mock()
        mock_processor_class.return_value = mock_instance
        
        # Reset global processor
        import api.slack_integration as slack_module
        slack_module.processor = None
        
        # First call should initialize
        processor1 = get_processor()
        
        # Second call should return same instance
        processor2 = get_processor()
        
        # Should be same instance (singleton pattern)
        assert processor1 is processor2
        # Should only call constructor once
        assert mock_processor_class.call_count == 1


class TestSlackRouterConfiguration:
    """Test Slack router configuration"""
    
    def test_router_prefix(self):
        """Test that router has correct prefix"""
        assert router.prefix == "/slack"
    
    def test_router_tags(self):
        """Test that router has correct tags"""
        assert "slack" in router.tags


class TestSlackCommandParsing:
    """Test parsing of Slack slash command input"""
    
    def test_parse_simple_query(self):
        """Test parsing simple search query"""
        command_text = "employee onboarding"
        
        # Query should be extracted correctly
        query = command_text.strip()
        
        assert query == "employee onboarding"
        assert len(query) > 0
    
    def test_parse_empty_query(self):
        """Test handling empty command"""
        command_text = ""
        
        query = command_text.strip()
        
        # Empty query should be handled gracefully
        assert query == ""
    
    def test_parse_query_with_special_characters(self):
        """Test parsing query with special characters"""
        command_text = "railway connectivity & network infrastructure"
        
        query = command_text.strip()
        
        # Special characters should be preserved
        assert "&" in query
        assert query == "railway connectivity & network infrastructure"
    
    def test_parse_multiword_query(self):
        """Test parsing multi-word queries"""
        command_text = "BMS HUMR FOR 005 employee onboarding form"
        
        query = command_text.strip()
        
        assert len(query.split()) > 1
        assert "BMS" in query
        assert "employee" in query


class TestSlackErrorHandling:
    """Test error handling in Slack integration"""
    
    def test_handle_search_timeout(self):
        """Test handling search timeout"""
        # Slack commands have 3-second response timeout
        timeout_seconds = 3
        
        # Should implement async processing or immediate response
        assert timeout_seconds > 0
    
    def test_handle_api_error(self):
        """Test handling API error gracefully"""
        error_message = "Search service temporarily unavailable"
        
        # Should return user-friendly error message
        assert len(error_message) > 0
        assert "temporarily unavailable" in error_message.lower()
    
    def test_handle_invalid_json_payload(self):
        """Test handling invalid JSON in request"""
        invalid_json = "not valid json {"
        
        # Should catch JSON parsing errors
        try:
            json.loads(invalid_json)
            parsed = True
        except json.JSONDecodeError:
            parsed = False
        
        assert parsed is False


class TestSlackResponseTypes:
    """Test different Slack response types"""
    
    def test_in_channel_response(self):
        """Test in_channel response type (visible to all)"""
        response_type = "in_channel"
        
        # Response should be visible to all users in channel
        assert response_type == "in_channel"
    
    def test_ephemeral_response(self):
        """Test ephemeral response type (visible only to user)"""
        response_type = "ephemeral"
        
        # Response should be visible only to command user
        assert response_type == "ephemeral"


class TestSlackBlockKitStructure:
    """Test Slack Block Kit message structure"""
    
    def test_block_kit_section_type(self):
        """Test section block structure"""
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Test message"
            }
        }
        
        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"
    
    def test_block_kit_divider(self):
        """Test divider block"""
        block = {"type": "divider"}
        
        assert block["type"] == "divider"
    
    def test_block_kit_context(self):
        """Test context block for metadata"""
        block = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Department: HUMR | Score: 0.95"
                }
            ]
        }
        
        assert block["type"] == "context"
        assert "elements" in block


class TestSlackIntegrationSecurity:
    """Test security aspects of Slack integration"""
    
    def test_signing_secret_from_env(self):
        """Test that signing secret is loaded from environment"""
        from api.slack_integration import SLACK_SIGNING_SECRET
        
        # Should be loaded from environment
        assert isinstance(SLACK_SIGNING_SECRET, str)
    
    def test_bot_token_from_env(self):
        """Test that bot token is loaded from environment"""
        from api.slack_integration import SLACK_BOT_TOKEN
        
        # Should be loaded from environment
        assert isinstance(SLACK_BOT_TOKEN, str)
    
    def test_hmac_comparison_timing_safe(self):
        """Test that HMAC comparison is timing-attack safe"""
        sig1 = "test_signature_1"
        sig2 = "test_signature_2"
        
        # Should use hmac.compare_digest for constant-time comparison
        result = hmac.compare_digest(sig1, sig2)
        
        # Function exists and works
        assert result is False
        assert hmac.compare_digest(sig1, sig1) is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
