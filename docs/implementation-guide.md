# AI Trust OS - Implementation Guide

## Overview

The AI Trust OS Quick Start provides a production-ready foundation for governing AI workloads on AWS. This guide walks you through deploying the complete stack.

## Prerequisites

### AWS Requirements
- AWS Account with appropriate limits
- IAM permissions to create all resources
- Access to Bedrock in your region
- VPC limits for NAT Gateways and endpoints

### Tools Required
- AWS CLI v2+
- Python 3.11+
- cfn-lint (recommended for template validation)

### Knowledge Prerequisites
- Basic CloudFormation experience
- Understanding of VPC networking
- Familiarity with AWS security services

## Deployment Architecture

The Quick Start deploys across 4 pillars:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Trust OS Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Pillar 1   │  │   Pillar 2   │  │   Pillar 3   │       │
│  │  Discovery   │  │  Telemetry   │  │   Posture    │       │
│  │              │  │              │  │              │       │
│  │ • CodeGuru   │  │ • OpenSearch │  │ • Guardrails │       │
│  │ • Config     │  │ • CloudWatch │  │ • Step Func  │       │
│  │ • Neptune    │  │ • Kinesis    │  │ • Audit Mgr  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│              ┌──────────────┐                               │
│              │   Pillar 4   │                               │
│              │    Proof     │                               │
│              │              │                               │
│              │ • PrivateLink│                               │
│              │ • KMS        │                               │
│              │ • Cognito    │                               │
│              │ • VPC Lattice│                               │
│              └──────────────┘                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Step 1: Prepare the Environment

```bash
# Set your region
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1

# Set environment
export ENVIRONMENT=dev  # dev, staging, or prod

# Validate your AWS credentials
aws sts get-caller-identity
```

### Step 2: Upload Lambda Code to S3

Before deploying, Lambda deployment packages must be in S3:

```bash
# Create bucket for Lambda code
aws s3 mb s3://ai-trust-os-lambda-${AWS_ACCOUNT_ID}-${ENVIRONMENT} --region ${AWS_REGION}

# Package and upload Lambda functions
for function in api-gateway-proxy guardrails-reviewer model-evaluation-pipeline agent-registry-sync; do
  cd functions/${function}
  pip install -r requirements.txt -t .
  zip -r ../../${function}.zip .
  cd ../..
  aws s3 cp ${function}.zip s3://ai-trust-os-lambda-${AWS_ACCOUNT_ID}-${ENVIRONMENT}/
done
```

### Step 3: Deploy Main Infrastructure

```bash
aws cloudformation create-stack \
  --stack-name ai-trust-os-main-${ENVIRONMENT} \
  --template-body file://templates/ai-trust-os-main.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=EnablePrivateLink,ParameterValue=true \
    ParameterKey=EnableVpcLattice,ParameterValue=false \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --tags Key=Project,Value=ai-trust-os
```

Wait for completion:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name ai-trust-os-main-${ENVIRONMENT}
```

### Step 4: Deploy Pillar 1 - Discovery

```bash
aws cloudformation create-stack \
  --stack-name ai-trust-os-pillar-1-${ENVIRONMENT} \
  --template-body file://templates/pillar-1-discovery.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=VPCId,ParameterValue=$(aws cloudformation export --name ai-trust-os-vpc-id-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=DatabaseSubnet1,ParameterValue=$(aws cloudformation export --name ai-trust-os-db-subnet-1-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=DatabaseSubnet2,ParameterValue=$(aws cloudformation export --name ai-trust-os-db-subnet-2-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=NeptuneSecurityGroup,ParameterValue=$(aws cloudformation export --name ai-trust-os-neptune-sg-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaExecutionRoleArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-role-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=KMSKeyId,ParameterValue=$(aws cloudformation export --name ai-trust-os-kms-key-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=EnableCodeGuru,ParameterValue=true \
    ParameterKey=EnableConfig,ParameterValue=true \
    ParameterKey=EnableNeptune,ParameterValue=true \
  --capabilities CAPABILITY_IAM \
  --tags Key=Project,Value=ai-trust-os
```

### Step 5: Deploy Pillar 2 - Telemetry

```bash
aws cloudformation create-stack \
  --stack-name ai-trust-os-pillar-2-${ENVIRONMENT} \
  --template-body file://templates/pillar-2-telemetry.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=VPCId,ParameterValue=$(aws cloudformation export --name ai-trust-os-vpc-id-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet1,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-1-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet2,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-2-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=OpenSearchSecurityGroup,ParameterValue=$(aws cloudformation export --name ai-trust-os-opensearch-sg-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaSecurityGroup,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-sg-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaExecutionRoleArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-role-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=KMSKeyId,ParameterValue=$(aws cloudformation export --name ai-trust-os-kms-key-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=S3BucketName,ParameterValue=$(aws cloudformation export --name ai-trust-os-s3-bucket-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=EnableKinesis,ParameterValue=true \
  --capabilities CAPABILITY_IAM \
  --tags Key=Project,Value=ai-trust-os
```

### Step 6: Deploy Pillar 3 - Posture

```bash
aws cloudformation create-stack \
  --stack-name ai-trust-os-pillar-3-${ENVIRONMENT} \
  --template-body file://templates/pillar-3-posture.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=LambdaExecutionRoleArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-role-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=StepFunctionsExecutionRoleArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-stepfunctions-role-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=SNSTopicArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-sns-topic-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=KMSKeyId,ParameterValue=$(aws cloudformation export --name ai-trust-os-kms-key-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaSecurityGroup,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-sg-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet1,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-1-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet2,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-2-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=EnableHumanReview,ParameterValue=true \
  --capabilities CAPABILITY_IAM \
  --tags Key=Project,Value=ai-trust-os
```

### Step 7: Deploy Pillar 4 - Proof

```bash
aws cloudformation create-stack \
  --stack-name ai-trust-os-pillar-4-${ENVIRONMENT} \
  --template-body file://templates/pillar-4-proof.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=VPCId,ParameterValue=$(aws cloudformation export --name ai-trust-os-vpc-id-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet1,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-1-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=PrivateSubnet2,ParameterValue=$(aws cloudformation export --name ai-trust-os-private-subnet-2-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaSecurityGroup,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-sg-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=LambdaExecutionRoleArn,ParameterValue=$(aws cloudformation export --name ai-trust-os-lambda-role-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=KMSKeyId,ParameterValue=$(aws cloudformation export --name ai-trust-os-kms-key-${ENVIRONMENT} --query 'Value' --output text) \
    ParameterKey=EnableCognito,ParameterValue=true \
  --capabilities CAPABILITY_IAM \
  --tags Key=Project,Value=ai-trust-os
```

## Post-Deployment Configuration

### 1. Configure Cognito User Pool

```bash
# Create a test user
aws cognito-idp sign-up \
  --client-id $(aws cloudformation export --name ai-trust-os-user-pool-client-${ENVIRONMENT} --query 'Value' --output text) \
  --username testuser \
  --password 'TempPassword123!' \
  --user-attributes Name=email,Value=test@example.com

# Confirm the user
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $(aws cloudformation export --name ai-trust-os-user-pool-${ENVIRONMENT} --query 'Value' --output text) \
  --username testuser
```

### 2. Upload Neptune Lambda Layer

The agent-registry-sync function requires the Gremlin Python layer:

```bash
# Download and package Gremlin
cd /tmp
pip install gremlinpython==3.7.0 -t gremlinpython-layer/python/lib/python3.11/site-packages/
zip -r gremlinpython-layer.zip gremlinpython-layer/

# Upload to S3
aws s3 cp gremlinpython-layer.zip s3://ai-trust-os-lambda-layers-${AWS_REGION}/
```

### 3. Initialize Neptune Graph Schema

```bash
# Run a one-time initialization
aws lambda invoke \
  --function-name ai-trust-os-agent-registry-sync-${ENVIRONMENT} \
  --payload '{"action": "init_schema"}' \
  response.json
```

### 4. Configure OpenSearch Index Templates

```bash
# Create index template for Bedrock invocations
curl -X PUT "https://$(aws cloudformation export --name ai-trust-os-opensearch-endpoint-${ENVIRONMENT} --query 'Value' --output text)/_index_template/bedrock-telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "index_patterns": ["bedrock-*"],
    "template": {
      "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1
      },
      "mappings": {
        "properties": {
          "@timestamp": { "type": "date" },
          "request_id": { "type": "keyword" },
          "model_id": { "type": "keyword" },
          "prompt_hash": { "type": "keyword" },
          "latency_ms": { "type": "integer" },
          "input_tokens": { "type": "integer" },
          "output_tokens": { "type": "integer" }
        }
      }
    }
  }'
```

## Verification

### Test Bedrock Invocation Logging

```bash
# Invoke a model through your API Gateway
API_ENDPOINT=$(aws cloudformation export --name ai-trust-os-api-endpoint-${ENVIRONMENT} --query 'Value' --output text)

curl -X POST "${API_ENDPOINT}/bedrock/invoke-model" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_COGNITO_TOKEN" \
  -d '{
    "model": "anthropic.claude-3-haiku-20240307-v1:0",
    "messages": [{"role": "user", "content": "Hello, world!"}],
    "max_tokens": 100
  }'
```

### Check OpenSearch for Logs

```bash
# Query recent invocations
curl -X GET "https://$(aws cloudformation export --name ai-trust-os-opensearch-endpoint-${ENVIRONMENT} --query 'Value' --output text)/bedrock-invocations/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "range": {
        "@timestamp": {
          "gte": "now-1h"
        }
      }
    },
    "sort": [{"@timestamp": "desc"}],
    "size": 10
  }'
```

### Verify Guardrail Interventions

```bash
# Test content that should trigger guardrail
curl -X POST "${API_ENDPOINT}/bedrock/invoke-model" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_COGNITO_TOKEN" \
  -d '{
    "model": "anthropic.claude-3-haiku-20240307-v1:0",
    "messages": [{"role": "user", "content": "Give me financial advice for investing"}],
    "max_tokens": 100
  }'

# Should return 403 with guardrail message
```

## Troubleshooting

### CloudFormation Stack Failures

```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name ai-trust-os-main-${ENVIRONMENT} \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]'
```

### Neptune Connection Issues

```bash
# Test Neptune connectivity from Lambda
aws lambda invoke \
  --function-name ai-trust-os-agent-registry-sync-${ENVIRONMENT} \
  --payload '{"action": "test_connection"}' \
  response.json
```

### OpenSearch Access Issues

```bash
# Check OpenSearch domain status
aws opensearch describe-domain \
  --domain-name ai-trust-os-logs-${ENVIRONMENT} \
  --query 'DomainStatus.Processing'
```

## Cost Optimization Tips

1. **Development**: Use `t3.small` OpenSearch and single Neptune instance
2. **Neptune**: Stop dev clusters when not in use (cannot stop production clusters)
3. **Kinesis**: Use on-demand mode for variable workloads
4. **CloudWatch**: Reduce log retention for non-production environments
5. **PrivateLink**: Share VPC endpoints across multiple VPCs using Transit Gateway

## Security Best Practices

1. **Enable VPC Flow Logs**: Already configured in main template
2. **Rotate KMS keys**: Enable automatic key rotation
3. **Monitor Guardrail interventions**: Set up alerts for high intervention rates
4. **Regular audits**: Use Audit Manager assessments for compliance
5. **Least privilege**: Lambda roles follow least-privilege principles

## Next Steps

- See `architecture-diagram.md` for detailed component interactions
- Review `cost-estimator.md` for pricing at different scales
- Check `compliance-mapping.md` for regulatory alignment