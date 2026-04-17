"""
AI Trust OS - Agent Registry Sync Lambda
Parses CloudTrail events and updates Neptune graph for AI asset discovery.
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib

# Initialize AWS clients
cloudtrail = boto3.client('cloudtrail')
neptune_client = boto3.client('neptune')
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
NEPTUNE_ENDPOINT = os.environ.get('NEPTUNE_ENDPOINT')
GRAPH_DB_NAME = os.environ.get('GRAPH_DB_NAME', 'aitrustos_graph')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

# Gremlin imports (would be in Lambda Layer)
try:
    from gremlin_python.driver.client import Client
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.structure.graph import Graph
    from gremlin_python.process.graph_traversal import __
    from gremlin_python.process.strategies import *
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False
    print("Gremlin not available - Neptune features disabled")


def lambda_handler(event, context):
    """
    Sync AI agent/asset information from CloudTrail to Neptune graph.
    
    Processes:
    - Bedrock model invocations
    - SageMaker endpoint deployments
    - Lambda function updates
    - IAM role changes
    - S3 access patterns
    """
    source = event.get('source', 'scheduled')
    
    if source == 'aws.cloudtrail':
        # Real-time CloudTrail event
        return _process_cloudtrail_event(event)
    
    elif 'Records' in event:
        # S3 notification with CloudTrail logs
        return _process_s3_cloudtrail_logs(event)
    
    else:
        # Scheduled sync - query CloudTrail and update graph
        return _scheduled_sync(event)


def _process_cloudtrail_event(event):
    """Process a real-time CloudTrail event."""
    try:
        detail = event.get('detail', {})
        event_name = detail.get('eventName')
        event_source = detail.get('eventSource')
        
        # Extract relevant AI asset information
        asset_info = _extract_asset_info(detail)
        
        if asset_info:
            # Update Neptune graph
            _update_graph(asset_info)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Asset updated in graph',
                    'asset_id': asset_info.get('id')
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'No relevant asset information found'})
        }
        
    except Exception as e:
        print(f"Error processing CloudTrail event: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _extract_asset_info(detail: Dict[str, Any]) -> Dict[str, Any]:
    """Extract AI asset information from CloudTrail detail."""
    event_name = detail.get('eventName')
    event_source = detail.get('eventSource')
    
    asset_info = None
    
    # Bedrock events
    if event_source == 'bedrock.amazonaws.com':
        if 'InvokeModel' in event_name:
            asset_info = {
                'type': 'bedrock_model',
                'id': _extract_model_id(detail),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn'),
                'source_ip': detail.get('sourceIPAddress'),
                'region': detail.get('awsRegion'),
                'request_params': detail.get('requestParameters', {}),
                'response_elements': detail.get('responseElements', {})
            }
        elif 'Guardrail' in event_name:
            asset_info = {
                'type': 'bedrock_guardrail',
                'id': _extract_guardrail_id(detail),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn'),
                'config': detail.get('requestParameters', {})
            }
    
    # SageMaker events
    elif event_source == 'sagemaker.amazonaws.com':
        if event_name in ['CreateEndpoint', 'UpdateEndpoint', 'DeleteEndpoint']:
            asset_info = {
                'type': 'sagemaker_endpoint',
                'id': _extract_endpoint_name(detail),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn'),
                'config': detail.get('requestParameters', {})
            }
        elif event_name in ['CreateModel', 'UpdateModel']:
            asset_info = {
                'type': 'sagemaker_model',
                'id': detail.get('requestParameters', {}).get('modelName'),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn')
            }
    
    # Lambda events
    elif event_source == 'lambda.amazonaws.com':
        if event_name in ['CreateFunction', 'UpdateFunctionConfiguration', 'UpdateFunctionCode']:
            asset_info = {
                'type': 'lambda_function',
                'id': _extract_lambda_name(detail),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn'),
                'runtime': detail.get('requestParameters', {}).get('runtime'),
                'environment_vars': list(detail.get('requestParameters', {}).get('environment', {}).get('variables', {}).keys())
            }
    
    # IAM events
    elif event_source == 'iam.amazonaws.com':
        if event_name in ['CreateRole', 'AttachRolePolicy', 'PutRolePolicy']:
            asset_info = {
                'type': 'iam_role',
                'id': _extract_role_name(detail),
                'event': event_name,
                'timestamp': detail.get('eventTime'),
                'user': detail.get('userIdentity', {}).get('arn'),
                'policies': _extract_attached_policies(detail)
            }
    
    return asset_info


def _extract_model_id(detail: Dict) -> str:
    """Extract model ID from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    return params.get('modelId', 'unknown')


def _extract_guardrail_id(detail: Dict) -> str:
    """Extract Guardrail ID from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    return params.get('guardrailIdentifier', 'unknown')


def _extract_endpoint_name(detail: Dict) -> str:
    """Extract SageMaker endpoint name from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    return params.get('endpointName', 'unknown')


def _extract_lambda_name(detail: Dict) -> str:
    """Extract Lambda function name from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    return params.get('functionName', params.get('name', 'unknown'))


def _extract_role_name(detail: Dict) -> str:
    """Extract IAM role name from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    return params.get('roleName', 'unknown')


def _extract_attached_policies(detail: Dict) -> List[str]:
    """Extract attached policy ARNs from CloudTrail detail."""
    params = detail.get('requestParameters', {})
    policies = []
    
    policy_arn = params.get('policyArn')
    if policy_arn:
        policies.append(policy_arn)
    
    policy_document = params.get('policyDocument')
    if policy_document:
        try:
            doc = json.loads(policy_document) if isinstance(policy_document, str) else policy_document
            policies.extend([stmt.get('Sid', 'statement') for stmt in doc.get('Statement', [])])
        except:
            pass
    
    return policies


def _update_graph(asset_info: Dict[str, Any]):
    """Update Neptune graph with asset information."""
    if not GREMLIN_AVAILABLE or not NEPTUNE_ENDPOINT:
        print("Graph update skipped - Neptune not available")
        return
    
    try:
        # Connect to Neptune
        remote_conn = DriverRemoteConnection(
            f'wss://{NEPTUNE_ENDPOINT}:8182/gremlin', 'g'
        )
        graph = Graph()
        g = graph.traversal().withRemote(remote_conn)
        
        # Create or update vertex
        asset_id = asset_info.get('id')
        asset_type = asset_info.get('type')
        
        # Check if vertex exists
        existing = g.V().has('asset', 'id', asset_id).toList()
        
        if existing:
            # Update existing vertex
            g.V().has('asset', 'id', asset_id) \
                .property('last_event', asset_info.get('event')) \
                .property('last_updated', asset_info.get('timestamp')) \
                .property('event_count', __.coalesce(__.values('event_count'), __.constant(0)).math('_ + 1')) \
                .next()
        else:
            # Create new vertex
            g.addV('asset') \
                .property('id', asset_id) \
                .property('type', asset_type) \
                .property('first_seen', asset_info.get('timestamp')) \
                .property('last_updated', asset_info.get('timestamp')) \
                .property('last_event', asset_info.get('event')) \
                .property('region', asset_info.get('region', 'unknown')) \
                .property('event_count', 1) \
                .next()
        
        # Create user relationship if applicable
        user = asset_info.get('user')
        if user:
            _upsert_user(g, user)
            _create_relationship(g, user, asset_id, 'ACCESSED', asset_info.get('timestamp'))
        
        remote_conn.close()
        
    except Exception as e:
        print(f"Error updating graph: {e}")


def _upsert_user(g, user_arn: str):
    """Create or update user vertex."""
    existing = g.V().has('user', 'arn', user_arn).toList()
    
    if not existing:
        g.addV('user') \
            .property('arn', user_arn) \
            .property('type', _extract_user_type(user_arn)) \
            .next()


def _extract_user_type(arn: str) -> str:
    """Extract user type from ARN."""
    if 'assumed-role' in arn:
        return 'assumed-role'
    elif ':role/' in arn:
        return 'role'
    elif ':user/' in arn:
        return 'user'
    elif 'lambda' in arn:
        return 'lambda'
    return 'unknown'


def _create_relationship(g, user_arn: str, asset_id: str, relationship: str, timestamp: str):
    """Create relationship edge between user and asset."""
    # Find user and asset vertices
    user_v = g.V().has('user', 'arn', user_arn).next()
    asset_v = g.V().has('asset', 'id', asset_id).next()
    
    # Create edge
    g.V(user_v).addE(relationship).to(asset_v) \
        .property('timestamp', timestamp) \
        .next()


def _scheduled_sync(event):
    """Perform scheduled sync from CloudTrail to Neptune."""
    try:
        # Look back period (default 5 minutes)
        lookback_minutes = event.get('lookback_minutes', 5)
        start_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
        
        # Query CloudTrail for relevant events
        lookup_attributes = [
            {'AttributeKey': 'EventSource', 'AttributeValue': 'bedrock.amazonaws.com'},
            {'AttributeKey': 'EventSource', 'AttributeValue': 'sagemaker.amazonaws.com'},
            {'AttributeKey': 'EventSource', 'AttributeValue': 'lambda.amazonaws.com'}
        ]
        
        all_events = []
        
        for attr in lookup_attributes:
            response = cloudtrail.lookup_events(
                LookupAttributes=[attr],
                StartTime=start_time,
                MaxResults=50
            )
            all_events.extend(response.get('Events', []))
        
        # Process events
        processed = 0
        for event in all_events:
            event_detail = json.loads(event.get('CloudTrailEvent', '{}'))
            asset_info = _extract_asset_info(event_detail)
            
            if asset_info:
                _update_graph(asset_info)
                processed += 1
        
        # Send summary notification
        if SNS_TOPIC_ARN and processed > 0:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f'[AI Trust OS] Agent Registry Sync - {ENVIRONMENT}',
                Message=json.dumps({
                    'sync_time': datetime.utcnow().isoformat(),
                    'events_processed': processed,
                    'lookback_minutes': lookback_minutes
                })
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'events_processed': processed,
                'sync_time': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in scheduled sync: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _process_s3_cloudtrail_logs(event):
    """Process CloudTrail logs delivered to S3."""
    try:
        processed = 0
        
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Download and parse log file
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse JSON
            for line in content.strip().split('\n'):
                if line:
                    log_entry = json.loads(line)
                    asset_info = _extract_asset_info(log_entry)
                    
                    if asset_info:
                        _update_graph(asset_info)
                        processed += 1
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'files_processed': len(event.get('Records', [])),
                'events_processed': processed
            })
        }
        
    except Exception as e:
        print(f"Error processing S3 logs: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# Discovery queries for Neptune
def discover_ai_assets(asset_type: str = None, region: str = None) -> List[Dict]:
    """
    Query Neptune to discover AI assets.
    
    Args:
        asset_type: Filter by asset type (bedrock_model, sagemaker_endpoint, etc.)
        region: Filter by AWS region
    
    Returns:
        List of discovered assets
    """
    if not GREMLIN_AVAILABLE or not NEPTUNE_ENDPOINT:
        return []
    
    try:
        remote_conn = DriverRemoteConnection(
            f'wss://{NEPTUNE_ENDPOINT}:8182/gremlin', 'g'
        )
        graph = Graph()
        g = graph.traversal().withRemote(remote_conn)
        
        # Build query
        query = g.V().hasLabel('asset')
        
        if asset_type:
            query = query.has('type', asset_type)
        
        if region:
            query = query.has('region', region)
        
        results = query.valueMap(True).toList()
        
        remote_conn.close()
        
        # Convert to list of dicts
        assets = []
        for result in results:
            asset = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in result.items()}
            assets.append(asset)
        
        return assets
        
    except Exception as e:
        print(f"Error discovering assets: {e}")
        return []


def get_asset_lineage(asset_id: str) -> Dict:
    """Get lineage and relationships for a specific asset."""
    if not GREMLIN_AVAILABLE or not NEPTUNE_ENDPOINT:
        return {}
    
    try:
        remote_conn = DriverRemoteConnection(
            f'wss://{NEPTUNE_ENDPOINT}:8182/gremlin', 'g'
        )
        graph = Graph()
        g = graph.traversal().withRemote(remote_conn)
        
        # Get asset details
        asset = g.V().has('asset', 'id', asset_id).valueMap(True).next()
        
        # Get relationships
        in_edges = g.V().has('asset', 'id', asset_id).inE().outV().valueMap(True).toList()
        out_edges = g.V().has('asset', 'id', asset_id).outE().inV().valueMap(True).toList()
        
        remote_conn.close()
        
        return {
            'asset': asset,
            'accessed_by': in_edges,
            'related_to': out_edges
        }
        
    except Exception as e:
        print(f"Error getting asset lineage: {e}")
        return {}