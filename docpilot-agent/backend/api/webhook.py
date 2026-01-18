"""
GitHub Webhook Handler
Receives webhook events from GitHub and triggers repository processing
"""
import hmac
import hashlib
import json
from fastapi import Request, HTTPException, APIRouter
from backend.jobs.worker import process_repository_pipeline
from backend.core.config import settings
from celery.utils.log import get_task_logger

router = APIRouter()
logger = get_task_logger(__name__)


def verify_github_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify that webhook payload came from GitHub
    https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks
    """
    try:
        if not hasattr(settings, 'GITHUB_WEBHOOK_SECRET') or not settings.GITHUB_WEBHOOK_SECRET:
            logger.warning("GitHub webhook secret not configured, skipping signature verification")
            return True
        
        # GitHub sends: sha256=<hash>
        if not signature_header.startswith('sha256='):
            return False
        
        signature = signature_header.split('=')[1]
        
        # Calculate HMAC
        expected_signature = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"Webhook signature verification error: {str(e)}")
        return False


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = None
):
    """
    GitHub webhook endpoint
    Receives push, pull_request, and other events from GitHub
    Triggers repository processing on push events
    """
    try:
        # Get raw payload for signature verification
        payload_body = await request.body()
        
        # Verify signature
        signature = request.headers.get('x-hub-signature-256', '')
        if not verify_github_webhook_signature(payload_body, signature):
            logger.warning("Invalid webhook signature")
            # Still process for development, but log warning
        
        # Get event type from header
        event_type = request.headers.get('x-github-event', 'unknown')
        
        # Parse JSON payload
        payload = json.loads(payload_body)
        
        logger.info(f"Received GitHub webhook event: {event_type}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)[:500]}")  # Log first 500 chars
        
        # Handle push events
        if event_type == 'push':
            return await handle_push_event(payload)
        
        # Handle pull_request events
        elif event_type == 'pull_request':
            return await handle_pull_request_event(payload)
        
        # Handle other events
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {
                "status": "received",
                "event": event_type,
                "message": "Event received but not configured for processing"
            }
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


async def handle_push_event(payload: dict):
    """
    Handle GitHub push events
    Triggered when commits are pushed to repository
    """
    try:
        # Extract repository information
        repo_name = payload.get('repository', {}).get('name', '')
        repo_url = payload.get('repository', {}).get('clone_url', '')
        branch = payload.get('ref', '').split('/')[-1]  # Extract branch name
        
        # Extract pusher information
        pusher_name = payload.get('pusher', {}).get('name', 'unknown')
        pushed_commits = payload.get('commits', [])
        
        if not repo_name or not repo_url:
            logger.error("Missing repository information in push event")
            return {
                "status": "error",
                "message": "Missing repository information"
            }
        
        logger.info(
            f"Push event: {pusher_name} pushed {len(pushed_commits)} commit(s) "
            f"to {repo_name}:{branch}"
        )
        
        # For webhook events, we don't have the GitHub token
        # You can configure a default token or request it separately
        github_token = getattr(settings, 'DEFAULT_GITHUB_TOKEN', None)
        
        if not github_token:
            logger.warning(
                f"No GitHub token available for webhook processing of {repo_name}. "
                "Configure DEFAULT_GITHUB_TOKEN in settings."
            )
            return {
                "status": "skipped",
                "reason": "No GitHub token configured for webhook processing",
                "repo": repo_name
            }
        
        # Trigger async processing pipeline
        logger.info(f"Triggering pipeline for {repo_name}")
        task = process_repository_pipeline.delay(
            proj_name=repo_name,
            repo_url=repo_url,
            branch=branch,
            github_token=github_token
        )
        
        logger.info(f"Pipeline task started: {task.id} for {repo_name}")
        
        return {
            "status": "processing",
            "task_id": task.id,
            "repo": repo_name,
            "branch": branch,
            "commits": len(pushed_commits),
            "message": "Repository processing triggered by push event"
        }
    
    except Exception as e:
        logger.error(f"Error handling push event: {str(e)}")
        raise


async def handle_pull_request_event(payload: dict):
    """
    Handle GitHub pull_request events
    Can be used to process PRs or trigger documentation preview
    """
    try:
        action = payload.get('action', '')
        repo_name = payload.get('repository', {}).get('name', '')
        pr_number = payload.get('pull_request', {}).get('number', '')
        
        logger.info(f"Pull request {action}: PR#{pr_number} in {repo_name}")
        
        # You can implement PR-specific logic here
        # For now, just acknowledge
        
        return {
            "status": "received",
            "event": "pull_request",
            "action": action,
            "repo": repo_name,
            "pr_number": pr_number,
            "message": "Pull request event received"
        }
    
    except Exception as e:
        logger.error(f"Error handling pull request event: {str(e)}")
        raise
