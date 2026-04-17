"""
AI Trust OS - Guardrails Reviewer Lambda
Polls Step Functions for human review tasks and manages the review workflow.
"""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

# Initialize AWS clients
stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock')

# Configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
REVIEW_TABLE = os.environ.get('REVIEW_TABLE')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Get DynamoDB table reference
review_table = dynamodb.Table(REVIEW_TABLE) if REVIEW_TABLE else None


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types for JSON serialization."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def lambda_handler(event, context):
    """
    Handle human review workflow.
    
    Triggered by:
    - Step Functions for new review tasks
    - API Gateway for review decisions
    - Scheduled events for cleanup
    """
    source = event.get('source', 'unknown')
    
    if source == 'aws.states':
        # Called from Step Functions - create review task
        return _create_review_task(event)
    
    elif 'httpMethod' in event:
        # API Gateway request - process review decision
        return _process_review_decision(event)
    
    elif source == 'aws.events':
        # Scheduled cleanup
        return _cleanup_expired_reviews()
    
    else:
        # Direct invocation - poll for pending reviews
        return _poll_pending_reviews()


def _create_review_task(event):
    """Create a new human review task from Step Functions."""
    try:
        content = event.get('content', '')
        guardrail_result = event.get('guardrail_result', {})
        execution_id = event.get('request_id', 'unknown')
        
        review_id = f"review-{execution_id}"
        created_at = datetime.utcnow().isoformat()
        
        # Store review task in DynamoDB
        if review_table:
            review_table.put_item(
                Item={
                    'review_id': review_id,
                    'status': 'PENDING',
                    'created_at': created_at,
                    'content_preview': content[:500] if content else '',  # Truncated for preview
                    'content_hash': _hash_content(content),
                    'guardrail_result': json.dumps(guardrail_result, cls=DecimalEncoder),
                    'execution_id': execution_id,
                    'reviewer_decision': None,
                    'reviewer_comments': None,
                    'reviewed_at': None,
                    'expiration_time': int((datetime.utcnow().timestamp() + 86400))  # 24 hours
                }
            )
        
        # Send notification to reviewers
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f'[AI Trust OS] Human Review Required - {ENVIRONMENT}',
                Message=json.dumps({
                    'review_id': review_id,
                    'status': 'PENDING',
                    'content_preview': content[:200] if content else 'Content blocked',
                    'guardrail_triggers': _extract_guardrail_triggers(guardrail_result),
                    'review_url': f'https://ai-trust-os.example.com/reviews/{review_id}',
                    'expires_in': '24 hours'
                }, indent=2)
            )
        
        return {
            'review_id': review_id,
            'status': 'PENDING',
            'message': 'Review task created and notification sent'
        }
        
    except Exception as e:
        print(f"Error creating review task: {e}")
        raise


def _process_review_decision(event):
    """Process a review decision from API Gateway."""
    try:
        body = json.loads(event.get('body', '{}'))
        review_id = body.get('review_id')
        decision = body.get('decision')  # APPROVE, REJECT, or MODIFY
        reviewer_comments = body.get('comments', '')
        
        if not review_id or not decision:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing review_id or decision'})
            }
        
        if decision not in ['APPROVE', 'REJECT', 'MODIFY']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid decision. Must be APPROVE, REJECT, or MODIFY'})
            }
        
        # Get review task
        if not review_table:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Review table not configured'})
            }
        
        response = review_table.get_item(Key={'review_id': review_id})
        review = response.get('Item')
        
        if not review:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Review task not found'})
            }
        
        if review.get('status') != 'PENDING':
            return {
                'statusCode': 409,
                'body': json.dumps({'error': f"Review already processed with status: {review['status']}"})
            }
        
        # Update review with decision
        reviewed_at = datetime.utcnow().isoformat()
        review_table.update_item(
            Key={'review_id': review_id},
            UpdateExpression='SET #status = :status, reviewer_decision = :decision, reviewer_comments = :comments, reviewed_at = :reviewed_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': decision,
                ':decision': decision,
                ':comments': reviewer_comments,
                ':reviewed_at': reviewed_at
            }
        )
        
        # Signal Step Functions if we have execution context
        execution_id = review.get('execution_id')
        if execution_id:
            # Note: In real implementation, you'd use task tokens
            pass
        
        # Send notification
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f'[AI Trust OS] Review Decision: {decision} - {ENVIRONMENT}',
                Message=json.dumps({
                    'review_id': review_id,
                    'decision': decision,
                    'reviewed_at': reviewed_at,
                    'reviewer_comments': reviewer_comments
                }, indent=2)
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'review_id': review_id,
                'decision': decision,
                'status': 'COMPLETED',
                'message': f'Review marked as {decision}'
            })
        }
        
    except Exception as e:
        print(f"Error processing review decision: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _poll_pending_reviews():
    """Poll for pending review tasks (used by Step Functions)."""
    try:
        if not review_table:
            return {'status': 'ERROR', 'message': 'Review table not configured'}
        
        # Query pending reviews
        response = review_table.query(
            IndexName='status-created-index',
            KeyConditionExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'PENDING'},
            Limit=10
        )
        
        pending_reviews = response.get('Items', [])
        
        # Check for expired reviews
        expired_count = 0
        for review in pending_reviews:
            expiration = review.get('expiration_time', 0)
            if expiration < datetime.utcnow().timestamp():
                review_table.update_item(
                    Key={'review_id': review['review_id']},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'EXPIRED'}
                )
                expired_count += 1
        
        return {
            'status': 'SUCCESS',
            'pending_count': len(pending_reviews) - expired_count,
            'expired_count': expired_count,
            'pending_reviews': [
                {
                    'review_id': r['review_id'],
                    'created_at': r['created_at'],
                    'content_preview': r.get('content_preview', '')
                }
                for r in pending_reviews if r.get('status') == 'PENDING'
            ]
        }
        
    except Exception as e:
        print(f"Error polling reviews: {e}")
        return {'status': 'ERROR', 'message': str(e)}


def _cleanup_expired_reviews():
    """Clean up expired review tasks."""
    try:
        if not review_table:
            return {'status': 'ERROR', 'message': 'Review table not configured'}
        
        # Scan for expired reviews
        current_time = int(datetime.utcnow().timestamp())
        
        response = review_table.scan(
            FilterExpression='expiration_time < :now AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':now': current_time,
                ':status': 'PENDING'
            }
        )
        
        expired_items = response.get('Items', [])
        
        for item in expired_items:
            review_table.update_item(
                Key={'review_id': item['review_id']},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'EXPIRED'}
            )
        
        return {
            'status': 'SUCCESS',
            'expired_count': len(expired_items)
        }
        
    except Exception as e:
        print(f"Error cleaning up reviews: {e}")
        return {'status': 'ERROR', 'message': str(e)}


def _hash_content(content: str) -> str:
    """Create hash of content."""
    import hashlib
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _extract_guardrail_triggers(guardrail_result: dict) -> list:
    """Extract human-readable guardrail triggers."""
    triggers = []
    
    if not guardrail_result:
        return triggers
    
    # Check topic policy
    topics = guardrail_result.get('outputs', [{}])[0].get('topicPolicy', {}).get('topics', [])
    for topic in topics:
        triggers.append(f"Topic: {topic.get('name', 'Unknown')}")
    
    # Check content policy
    filters = guardrail_result.get('outputs', [{}])[0].get('contentPolicy', {}).get('filters', [])
    for filter_item in filters:
        triggers.append(f"Content: {filter_item.get('type', 'Unknown')} ({filter_item.get('confidence', 'Unknown')})")
    
    # Check PII
    pii = guardrail_result.get('outputs', [{}])[0].get('sensitiveInformationPolicy', {}).get('piiEntities', [])
    for entity in pii:
        triggers.append(f"PII: {entity.get('type', 'Unknown')}")
    
    return triggers


# For direct Lambda invocation from Step Functions
def check_review_status(event, context):
    """
    Check the status of a review task.
    Called by Step Functions to determine workflow path.
    """
    review_id = event.get('review_id') or event.get('Payload', {}).get('review_id')
    
    if not review_id or not review_table:
        return {'decision': 'REJECT', 'reason': 'Missing review context'}
    
    try:
        response = review_table.get_item(Key={'review_id': review_id})
        review = response.get('Item')
        
        if not review:
            return {'decision': 'REJECT', 'reason': 'Review not found'}
        
        status = review.get('status')
        
        if status == 'APPROVE':
            return {
                'decision': 'APPROVE',
                'review_id': review_id,
                'reviewed_at': review.get('reviewed_at')
            }
        elif status == 'MODIFY':
            return {
                'decision': 'MODIFY',
                'review_id': review_id,
                'reviewed_at': review.get('reviewed_at'),
                'comments': review.get('reviewer_comments')
            }
        elif status in ['REJECT', 'EXPIRED']:
            return {
                'decision': 'REJECT',
                'review_id': review_id,
                'reason': review.get('reviewer_comments', 'Content rejected')
            }
        else:
            # Still pending
            return {
                'decision': 'PENDING',
                'review_id': review_id,
                'created_at': review.get('created_at')
            }
            
    except Exception as e:
        print(f"Error checking review status: {e}")
        return {'decision': 'REJECT', 'reason': str(e)}