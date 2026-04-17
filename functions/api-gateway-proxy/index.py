"""
AI Trust OS - API Gateway Proxy Lambda
Captures OpenAI/Anthropic API calls and logs to OpenSearch for audit and telemetry.
"""
import json
import boto3
import os
import hashlib
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime')
bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')
kms = boto3.client('kms')

# Configuration from environment
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')
GUARDRAIL_ID = os.environ.get('GUARDRAIL_ID')
OPENSEARCH_DOMAIN = os.environ.get('OPENSEARCH_DOMAIN')
S3_BUCKET = os.environ.get('S3_BUCKET')


def lambda_handler(event, context):
    """
    API Gateway proxy handler for AI model invocations.
    
    Captures and logs all API calls with:
    - Request/response payload hashes (for privacy)
    - Token counts and latency
    - User identity
    - Guardrail evaluation results
    """
    request_id = context.aws_request_id
    start_time = time.time()
    
    try:
        # Parse API Gateway request
        body = json.loads(event.get('body', '{}'))
        headers = event.get('headers', {})
        
        # Extract model and provider info
        model_id = body.get('model', 'unknown')
        provider = _detect_provider(model_id, headers)
        
        # Hash sensitive content (don't store raw prompts)
        prompt_hash = _hash_content(json.dumps(body.get('messages', body.get('prompt', ''))))
        
        # Apply Bedrock Guardrails if configured
        guardrail_result = None
        if GUARDRAIL_ID:
            guardrail_result = _apply_guardrail(body)
            if guardrail_result.get('action') == 'BLOCKED':
                return _create_blocked_response(guardrail_result, request_id)
        
        # Call the actual model (Bedrock)
        response, invocation_metrics = _invoke_bedrock_model(model_id, body)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Hash response content
        response_hash = _hash_content(json.dumps(response.get('content', response.get('completion', ''))))
        
        # Log telemetry
        telemetry_record = {
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'model_id': model_id,
            'provider': provider,
            'prompt_hash': prompt_hash,
            'response_hash': response_hash,
            'input_tokens': invocation_metrics.get('inputTokens', 0),
            'output_tokens': invocation_metrics.get('outputTokens', 0),
            'latency_ms': latency_ms,
            'user_arn': event.get('requestContext', {}).get('identity', {}).get('userArn'),
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
            'guardrail_intervened': guardrail_result is not None,
            'guardrail_action': guardrail_result.get('action') if guardrail_result else None,
            'environment': ENVIRONMENT
        }
        
        # Async log to OpenSearch and S3
        _log_telemetry(telemetry_record)
        
        # Return API Gateway response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Request-ID': request_id,
                'X-Guardrail-Checked': 'true' if guardrail_result else 'false'
            },
            'body': json.dumps(response)
        }
        
    except Exception as e:
        # Log error
        error_record = {
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'error_type': type(e).__name__,
            'environment': ENVIRONMENT
        }
        _log_telemetry(error_record, index='bedrock-errors')
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'request_id': request_id
            })
        }


def _detect_provider(model_id: str, headers: dict) -> str:
    """Detect AI provider based on model ID and headers."""
    model_lower = model_id.lower()
    
    if 'claude' in model_lower or 'anthropic' in str(headers).lower():
        return 'anthropic'
    elif 'gpt' in model_lower or 'openai' in str(headers).lower():
        return 'openai'
    elif 'amazon' in model_lower or 'titan' in model_lower:
        return 'amazon'
    elif 'meta' in model_lower or 'llama' in model_lower:
        return 'meta'
    elif 'ai21' in model_lower or 'jurassic' in model_lower:
        return 'ai21'
    elif 'cohere' in model_lower:
        return 'cohere'
    else:
        return 'unknown'


def _hash_content(content: str) -> str:
    """Create SHA-256 hash of content for privacy-preserving logging."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def _apply_guardrail(body: dict) -> dict:
    """Apply Bedrock Guardrail to the request."""
    try:
        content = json.dumps(body.get('messages', body.get('prompt', '')))
        
        response = bedrock.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion='DRAFT',
            content=[
                {
                    'text': {
                        'text': content[:100000]  # Guardrail has size limits
                    }
                }
            ],
            source='INPUT'
        )
        
        return {
            'action': response.get('action', 'NONE'),
            'outputs': response.get('outputs', []),
            'assessments': response.get('assessments', [])
        }
    except Exception as e:
        print(f"Guardrail application failed: {e}")
        return {'action': 'NONE', 'error': str(e)}


def _invoke_bedrock_model(model_id: str, body: dict) -> tuple:
    """Invoke Bedrock model and return response with metrics."""
    # Prepare request body for Bedrock
    bedrock_body = _transform_to_bedrock_format(body, model_id)
    
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(bedrock_body),
        accept='application/json',
        contentType='application/json'
    )
    
    response_body = json.loads(response['body'].read())
    
    # Extract metrics from response headers
    metrics = {
        'inputTokens': int(response['ResponseMetadata']['HTTPHeaders'].get('x-amzn-bedrock-input-token-count', 0)),
        'outputTokens': int(response['ResponseMetadata']['HTTPHeaders'].get('x-amzn-bedrock-output-token-count', 0))
    }
    
    return response_body, metrics


def _transform_to_bedrock_format(body: dict, model_id: str) -> dict:
    """Transform OpenAI-style request to Bedrock format."""
    if 'anthropic' in model_id.lower() or 'claude' in model_id.lower():
        # Claude format
        messages = body.get('messages', [])
        return {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': body.get('max_tokens', 1024),
            'messages': messages,
            'temperature': body.get('temperature', 0.7),
            'top_p': body.get('top_p', 0.9)
        }
    elif 'amazon' in model_id.lower():
        # Titan format
        return {
            'inputText': body.get('prompt', ''),
            'textGenerationConfig': {
                'maxTokenCount': body.get('max_tokens', 1024),
                'temperature': body.get('temperature', 0.7),
                'topP': body.get('top_p', 0.9)
            }
        }
    else:
        # Generic format
        return {
            'prompt': body.get('prompt', ''),
            'maxTokens': body.get('max_tokens', 1024),
            'temperature': body.get('temperature', 0.7)
        }


def _create_blocked_response(guardrail_result: dict, request_id: str) -> dict:
    """Create response when content is blocked by guardrail."""
    return {
        'statusCode': 403,
        'headers': {
            'Content-Type': 'application/json',
            'X-Request-ID': request_id,
            'X-Guardrail-Action': 'BLOCKED'
        },
        'body': json.dumps({
            'error': 'Content blocked by safety guardrails',
            'request_id': request_id,
            'guardrail_action': guardrail_result.get('action'),
            'message': 'This content violates usage policies. Please modify your request.'
        })
    }


def _log_telemetry(record: dict, index: str = 'bedrock-invocations'):
    """Log telemetry to OpenSearch and S3."""
    try:
        # Async log to S3
        if S3_BUCKET:
            timestamp = datetime.utcnow()
            s3_key = f"telemetry/{index}/year={timestamp.year}/month={timestamp.month:02d}/day={timestamp.day:02d}/{record['request_id']}.json"
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(record),
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=KMS_KEY_ID
            )
        
        # Log to OpenSearch if configured
        if OPENSEARCH_DOMAIN:
            _index_to_opensearch(record, index)
            
    except Exception as e:
        print(f"Failed to log telemetry: {e}")


def _index_to_opensearch(record: dict, index: str):
    """Index record to OpenSearch."""
    try:
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        
        url = f"https://{OPENSEARCH_DOMAIN}/{index}/_doc/{record['request_id']}"
        
        request = AWSRequest(method='POST', url=url, data=json.dumps(record))
        request.headers['Content-Type'] = 'application/json'
        
        credentials = boto3.Session().get_credentials()
        SigV4Auth(credentials, 'es', boto3.Session().region_name).add_auth(request)
        
        req = Request(
            url,
            data=json.dumps(record).encode('utf-8'),
            headers=dict(request.headers)
        )
        
        response = urlopen(req, timeout=10)
        return response.read()
        
    except Exception as e:
        print(f"OpenSearch indexing failed: {e}")