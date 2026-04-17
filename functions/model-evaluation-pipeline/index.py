"""
AI Trust OS - Model Evaluation Pipeline Lambda
Triggers Bedrock Evaluations and stores results for continuous model monitoring.
"""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import time

# Initialize AWS clients
bedrock = boto3.client('bedrock')
s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
S3_BUCKET = os.environ.get('S3_BUCKET')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
EVALUATION_TABLE = os.environ.get('EVALUATION_TABLE', 'ai-trust-os-evaluations')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Get DynamoDB table
evaluation_table = dynamodb.Table(EVALUATION_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types for JSON serialization."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def lambda_handler(event, context):
    """
    Trigger and manage Bedrock model evaluations.
    
    Supports:
    - Automatic evaluation (accuracy, robustness, toxicity)
    - Human evaluation (quality, relevance, style)
    - Scheduled evaluation runs
    - Results processing and alerting
    """
    action = event.get('action', 'trigger_evaluation')
    
    if action == 'trigger_evaluation':
        return _trigger_evaluation(event)
    elif action == 'process_results':
        return _process_evaluation_results(event)
    elif action == 'schedule_evaluations':
        return _schedule_evaluations(event)
    elif action == 'get_evaluation_status':
        return _get_evaluation_status(event)
    elif action == 'list_evaluations':
        return _list_evaluations(event)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown action: {action}'})
        }


def _trigger_evaluation(event):
    """Trigger a new Bedrock evaluation job."""
    try:
        model_id = event.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
        evaluation_type = event.get('evaluation_type', 'automated')  # automated or human
        dataset_location = event.get('dataset_location')
        
        if not dataset_location and S3_BUCKET:
            # Use default evaluation dataset
            dataset_location = f's3://{S3_BUCKET}/evaluation-datasets/default.jsonl'
        
        evaluation_name = event.get('evaluation_name', f"eval-{model_id.replace('.', '-')}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
        
        # Create evaluation job configuration
        if evaluation_type == 'automated':
            job_config = _create_automated_evaluation_config(
                model_id=model_id,
                dataset_location=dataset_location,
                evaluation_name=evaluation_name,
                metrics=event.get('metrics', ['accuracy', 'robustness', 'toxicity'])
            )
        else:
            job_config = _create_human_evaluation_config(
                model_id=model_id,
                dataset_location=dataset_location,
                evaluation_name=evaluation_name,
                custom_metrics=event.get('custom_metrics')
            )
        
        # Start evaluation job
        response = bedrock.start_evaluation_job(**job_config)
        
        job_arn = response.get('jobArn')
        job_id = job_arn.split('/')[-1] if job_arn else 'unknown'
        
        # Store evaluation metadata
        evaluation_record = {
            'evaluation_id': job_id,
            'job_arn': job_arn,
            'model_id': model_id,
            'evaluation_type': evaluation_type,
            'evaluation_name': evaluation_name,
            'status': 'InProgress',
            'created_at': datetime.utcnow().isoformat(),
            'dataset_location': dataset_location,
            'metrics': json.dumps(event.get('metrics', []), cls=DecimalEncoder),
            'created_by': event.get('created_by', 'system'),
            'environment': ENVIRONMENT
        }
        
        evaluation_table.put_item(Item=evaluation_record)
        
        # Send notification
        if SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f'[AI Trust OS] Evaluation Started - {ENVIRONMENT}',
                Message=json.dumps({
                    'evaluation_id': job_id,
                    'model_id': model_id,
                    'evaluation_type': evaluation_type,
                    'status': 'InProgress',
                    'created_at': evaluation_record['created_at']
                }, indent=2)
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'evaluation_id': job_id,
                'job_arn': job_arn,
                'status': 'InProgress',
                'message': f'Evaluation started for {model_id}'
            })
        }
        
    except Exception as e:
        print(f"Error triggering evaluation: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _create_automated_evaluation_config(model_id, dataset_location, evaluation_name, metrics):
    """Create configuration for automated evaluation."""
    config = {
        'jobName': evaluation_name,
        'roleArn': os.environ.get('EVALUATION_ROLE_ARN'),
        'model': {
            'modelIdentifier': model_id
        },
        'evaluationConfig': {
            'automated': {
                'dataset': {
                    'name': 'evaluation-dataset',
                    'location': {
                        's3Uri': dataset_location
                    }
                },
                'metricNames': metrics,
                'taskType': 'general'
            }
        },
        'outputDataConfig': {
            's3Uri': f's3://{S3_BUCKET}/evaluation-results/'
        }
    }
    
    # Add KMS encryption if configured
    if KMS_KEY_ID:
        config['outputDataConfig']['kmsKeyId'] = KMS_KEY_ID
    
    return config


def _create_human_evaluation_config(model_id, dataset_location, evaluation_name, custom_metrics):
    """Create configuration for human evaluation."""
    default_metrics = [
        {'name': 'quality', 'description': 'Overall quality of the response'},
        {'name': 'relevance', 'description': 'Relevance to the prompt'},
        {'name': 'helpfulness', 'description': 'Helpfulness of the response'}
    ]
    
    metrics = custom_metrics if custom_metrics else default_metrics
    
    config = {
        'jobName': evaluation_name,
        'roleArn': os.environ.get('EVALUATION_ROLE_ARN'),
        'model': {
            'modelIdentifier': model_id
        },
        'evaluationConfig': {
            'human': {
                'dataset': {
                    'name': 'evaluation-dataset',
                    'location': {
                        's3Uri': dataset_location
                    }
                },
                'humanEvaluationConfig': {
                    'humanEvaluationCriteria': metrics,
                    'numEvaluationsPerPrompt': 3  # Number of human reviewers per prompt
                }
            }
        },
        'outputDataConfig': {
            's3Uri': f's3://{S3_BUCKET}/evaluation-results/'
        }
    }
    
    if KMS_KEY_ID:
        config['outputDataConfig']['kmsKeyId'] = KMS_KEY_ID
    
    return config


def _process_evaluation_results(event):
    """Process completed evaluation results."""
    try:
        evaluation_id = event.get('evaluation_id')
        
        if not evaluation_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing evaluation_id'})
            }
        
        # Get evaluation job details
        response = bedrock.get_evaluation_job(
            jobIdentifier=evaluation_id
        )
        
        status = response.get('status')
        
        # Update DynamoDB record
        update_expr = 'SET #status = :status, updated_at = :updated_at'
        expr_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        expr_names = {'#status': 'status'}
        
        # If completed, process results
        if status == 'Completed':
            results_location = response.get('outputDataConfig', {}).get('s3Uri')
            
            # Download and parse results
            results = _download_evaluation_results(results_location)
            
            # Extract key metrics
            metrics_summary = _extract_metrics_summary(results)
            
            update_expr += ', results_location = :results_loc, metrics_summary = :metrics'
            expr_values[':results_loc'] = results_location
            expr_values[':metrics'] = json.dumps(metrics_summary, cls=DecimalEncoder)
            
            # Check for concerning results
            alerts = _check_thresholds(metrics_summary)
            
            if alerts:
                update_expr += ', alerts = :alerts'
                expr_values[':alerts'] = json.dumps(alerts, cls=DecimalEncoder)
                
                # Send alert notification
                if SNS_TOPIC_ARN:
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Subject=f'[AI Trust OS] Evaluation Alerts - {ENVIRONMENT}',
                        Message=json.dumps({
                            'evaluation_id': evaluation_id,
                            'alerts': alerts,
                            'model_id': response.get('model', {}).get('modelIdentifier'),
                            'metrics_summary': metrics_summary
                        }, indent=2)
                    )
        
        elif status in ['Failed', 'Stopped']:
            failure_reason = response.get('failureReason', 'Unknown error')
            update_expr += ', failure_reason = :reason'
            expr_values[':reason'] = failure_reason
        
        evaluation_table.update_item(
            Key={'evaluation_id': evaluation_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'evaluation_id': evaluation_id,
                'status': status,
                'message': 'Results processed successfully'
            })
        }
        
    except Exception as e:
        print(f"Error processing evaluation results: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _schedule_evaluations(event):
    """Schedule periodic evaluations for registered models."""
    try:
        # List of models to evaluate
        models = event.get('models', [
            'anthropic.claude-3-sonnet-20240229-v1:0',
            'anthropic.claude-3-haiku-20240307-v1:0',
            'amazon.titan-text-express-v1'
        ])
        
        scheduled = []
        
        for model_id in models:
            # Trigger evaluation for each model
            result = _trigger_evaluation({
                'model_id': model_id,
                'evaluation_type': 'automated',
                'evaluation_name': f'scheduled-{model_id.replace(".", "-")}-{datetime.utcnow().strftime("%Y%m%d")}'
            })
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                scheduled.append({
                    'model_id': model_id,
                    'evaluation_id': body.get('evaluation_id')
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'scheduled_count': len(scheduled),
                'scheduled_evaluations': scheduled
            })
        }
        
    except Exception as e:
        print(f"Error scheduling evaluations: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _get_evaluation_status(event):
    """Get status of a specific evaluation."""
    try:
        evaluation_id = event.get('evaluation_id')
        
        # Get from DynamoDB
        response = evaluation_table.get_item(
            Key={'evaluation_id': evaluation_id}
        )
        
        record = response.get('Item')
        
        if not record:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Evaluation not found'})
            }
        
        # Also get fresh status from Bedrock if still in progress
        if record.get('status') == 'InProgress':
            try:
                bedrock_response = bedrock.get_evaluation_job(
                    jobIdentifier=evaluation_id
                )
                record['bedrock_status'] = bedrock_response.get('status')
            except Exception as e:
                print(f"Could not get Bedrock status: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(record, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error getting evaluation status: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _list_evaluations(event):
    """List recent evaluations with optional filtering."""
    try:
        model_id = event.get('model_id')
        status = event.get('status')
        limit = event.get('limit', 20)
        
        # Scan with filter
        filter_expr = None
        expr_values = {}
        expr_names = {}
        
        if model_id:
            filter_expr = 'model_id = :model_id'
            expr_values[':model_id'] = model_id
        
        if status:
            if filter_expr:
                filter_expr += ' AND #status = :status'
            else:
                filter_expr = '#status = :status'
            expr_values[':status'] = status
            expr_names['#status'] = 'status'
        
        scan_kwargs = {'Limit': limit}
        
        if filter_expr:
            scan_kwargs['FilterExpression'] = filter_expr
            scan_kwargs['ExpressionAttributeValues'] = expr_values
        
        if expr_names:
            scan_kwargs['ExpressionAttributeNames'] = expr_names
        
        response = evaluation_table.scan(**scan_kwargs)
        
        # Sort by created_at descending
        items = sorted(
            response.get('Items', []),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'evaluations': items,
                'count': len(items)
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error listing evaluations: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _download_evaluation_results(s3_uri):
    """Download evaluation results from S3."""
    try:
        # Parse S3 URI
        bucket_key = s3_uri.replace('s3://', '').split('/', 1)
        bucket = bucket_key[0]
        key = bucket_key[1] if len(bucket_key) > 1 else ''
        
        # Download results file
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Parse JSON lines
        results = [json.loads(line) for line in content.strip().split('\n') if line]
        
        return results
        
    except Exception as e:
        print(f"Error downloading results: {e}")
        return []


def _extract_metrics_summary(results):
    """Extract summary metrics from evaluation results."""
    if not results:
        return {}
    
    summary = {
        'total_evaluations': len(results),
        'metrics': {}
    }
    
    # Aggregate metrics
    for result in results:
        metrics = result.get('metrics', {})
        for metric_name, value in metrics.items():
            if metric_name not in summary['metrics']:
                summary['metrics'][metric_name] = []
            summary['metrics'][metric_name].append(value)
    
    # Calculate averages
    for metric_name, values in summary['metrics'].items():
        if values:
            summary['metrics'][metric_name] = {
                'average': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
    
    return summary


def _check_thresholds(metrics_summary):
    """Check if any metrics breach defined thresholds."""
    alerts = []
    
    # Define thresholds
    thresholds = {
        'toxicity': {'max': 0.1, 'severity': 'HIGH'},
        'bias': {'max': 0.15, 'severity': 'HIGH'},
        'accuracy': {'min': 0.7, 'severity': 'MEDIUM'},
        'robustness': {'min': 0.6, 'severity': 'MEDIUM'}
    }
    
    for metric_name, metric_data in metrics_summary.get('metrics', {}).items():
        if metric_name in thresholds:
            threshold = thresholds[metric_name]
            avg_value = metric_data.get('average', 0)
            
            if 'max' in threshold and avg_value > threshold['max']:
                alerts.append({
                    'metric': metric_name,
                    'value': avg_value,
                    'threshold': threshold['max'],
                    'severity': threshold['severity'],
                    'message': f'{metric_name} ({avg_value:.3f}) exceeds threshold ({threshold["max"]})'
                })
            
            if 'min' in threshold and avg_value < threshold['min']:
                alerts.append({
                    'metric': metric_name,
                    'value': avg_value,
                    'threshold': threshold['min'],
                    'severity': threshold['severity'],
                    'message': f'{metric_name} ({avg_value:.3f}) below threshold ({threshold["min"]})'
                })
    
    return alerts


# For scheduled invocations
def scheduled_evaluation_runner(event, context):
    """
    Entry point for scheduled evaluation runs.
    Triggered by CloudWatch Events/EventBridge.
    """
    return _schedule_evaluations({
        'action': 'schedule_evaluations',
        'models': event.get('models')
    })