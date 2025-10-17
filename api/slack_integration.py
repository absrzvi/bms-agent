"""
Slack Integration for BMS Agent
Provides slash commands and interactive messaging for document search
"""

import os
import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import requests

from api.processor_wrapper import BMSDocumentProcessor

router = APIRouter(prefix="/slack", tags=["slack"])

# Slack configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

# Initialize processor for search
processor = None

def get_processor():
    """Get or initialize the BMS processor"""
    global processor
    if processor is None:
        processor = BMSDocumentProcessor()
    return processor


def verify_slack_signature(
    signing_secret: str,
    timestamp: str,
    body: bytes,
    signature: str
) -> bool:
    """
    Verify that the request came from Slack
    
    Args:
        signing_secret: Slack app signing secret
        timestamp: Request timestamp from headers
        body: Raw request body
        signature: Slack signature from headers
    
    Returns:
        True if signature is valid
    """
    if not signing_secret:
        # POC mode: skip verification if no secret configured
        return True
    
    # Check timestamp to prevent replay attacks
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    # Compute signature
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)


def format_search_results_for_slack(results: List[Dict], query: str) -> Dict[str, Any]:
    """
    Format search results as Slack Block Kit message
    
    Args:
        results: Search results from BMS API
        query: Original search query
    
    Returns:
        Slack message payload with blocks
    """
    if not results:
        return {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🔍 No results found for: *{query}*"
                    }
                }
            ]
        }
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🔍 Found *{len(results)}* results for: *{query}*"
            }
        },
        {"type": "divider"}
    ]
    
    for i, result in enumerate(results[:5], 1):  # Limit to top 5
        payload = result.get("payload", {})
        score = result.get("score", 0.0)
        
        doc_name = payload.get("document_name", "Unknown")
        doc_type = payload.get("document_type", "unknown")
        quality = payload.get("quality_score", 0.0)
        content = payload.get("content", "")
        
        # Truncate content for Slack
        content_preview = content[:200] + "..." if len(content) > 200 else content
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{i}. {doc_name}*\n"
                    f"📄 Type: `{doc_type}` | Quality: `{quality:.2f}` | Relevance: `{score:.3f}`\n"
                    f"_{content_preview}_"
                )
            }
        })
    
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Searched 448 documents | Powered by BMS Agent"
            }
        ]
    })
    
    return {
        "response_type": "in_channel",
        "blocks": blocks
    }


@router.post("/slash-command")
async def handle_slash_command(
    request: Request,
    x_slack_request_timestamp: Optional[str] = Header(None),
    x_slack_signature: Optional[str] = Header(None)
):
    """
    Handle Slack slash commands like /bms-search
    
    Supported commands:
    - /bms-search [query] - Semantic search
    - /bms-search-hybrid [query] - Hybrid search
    - /bms-help - Show help
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify Slack signature (POC: optional)
    if SLACK_SIGNING_SECRET and x_slack_signature and x_slack_request_timestamp:
        if not verify_slack_signature(
            SLACK_SIGNING_SECRET,
            x_slack_request_timestamp,
            body,
            x_slack_signature
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse form data
    form_data = await request.form()
    command = form_data.get("command", "")
    text = form_data.get("text", "").strip()
    user_name = form_data.get("user_name", "unknown")
    
    # Handle help command
    if command == "/bms-help" or text.lower() == "help":
        return JSONResponse({
            "response_type": "ephemeral",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            "*BMS Agent - Railway Documentation Search*\n\n"
                            "*Available Commands:*\n"
                            "• `/bms-search [query]` - Semantic search using AI\n"
                            "• `/bms-search-hybrid [query]` - Hybrid search (semantic + keyword)\n"
                            "• `/bms-help` - Show this help message\n\n"
                            "*Examples:*\n"
                            "• `/bms-search business continuity planning`\n"
                            "• `/bms-search-hybrid railway safety procedures`\n\n"
                            "_Searching 448 indexed documents with 0.714 quality score_"
                        )
                    }
                }
            ]
        })
    
    # Validate query
    if not text:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "❌ Please provide a search query. Example: `/bms-search business continuity`"
        })
    
    # Determine search type
    search_type = "hybrid" if "hybrid" in command else "semantic"
    
    # Perform search via BMS API
    try:
        api_url = f"http://localhost:8000/api/v1/search/{search_type}"
        response = requests.post(
            api_url,
            json={"query": text, "limit": 5},
            timeout=30
        )
        
        if response.status_code != 200:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": f"❌ Search failed: {response.status_code}"
            })
        
        data = response.json()
        results = data.get("results", [])
        
        # Format and return results
        return JSONResponse(format_search_results_for_slack(results, text))
        
    except requests.exceptions.Timeout:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": "❌ Search timed out. Please try again."
        })
    except Exception as e:
        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"❌ Error: {str(e)}"
        })


@router.post("/events")
async def handle_events(
    request: Request,
    x_slack_request_timestamp: Optional[str] = Header(None),
    x_slack_signature: Optional[str] = Header(None)
):
    """
    Handle Slack Events API (for @mentions, etc.)
    """
    body = await request.body()
    
    # Verify signature
    if SLACK_SIGNING_SECRET and x_slack_signature and x_slack_request_timestamp:
        if not verify_slack_signature(
            SLACK_SIGNING_SECRET,
            x_slack_request_timestamp,
            body,
            x_slack_signature
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    
    # Handle URL verification challenge
    if data.get("type") == "url_verification":
        return JSONResponse({"challenge": data.get("challenge")})
    
    # Handle app mention events
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        
        if event.get("type") == "app_mention":
            # Extract query from mention
            text = event.get("text", "")
            # Remove bot mention
            query = text.split(">", 1)[-1].strip() if ">" in text else text.strip()
            
            if not query or query.lower() == "help":
                # Send help message
                return JSONResponse({"ok": True})
            
            # Perform search and respond
            # Note: For async responses, use Slack Web API
            return JSONResponse({"ok": True})
    
    return JSONResponse({"ok": True})


@router.get("/health")
async def slack_health():
    """Health check for Slack integration"""
    return {
        "status": "healthy",
        "slack_configured": bool(SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET),
        "endpoints": [
            "/slack/slash-command",
            "/slack/events",
            "/slack/health"
        ]
    }
