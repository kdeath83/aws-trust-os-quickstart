# AI Trust OS - Cost Estimator

> ⚠️ **IMPORTANT: These are baseline (unoptimized) costs.** 
> 
> The scenarios below show what AI Trust OS costs **without any optimizations**. 
> With the [cost-optimized.json](../config/cost-optimized.json) configuration, you can achieve:
> - **Dev: $75/mo instead of $441** (83% savings)
> - **Small Prod: $1,800/mo instead of $11,866** (85% savings)  
> - **Large Prod: $28,000/mo instead of $146,310** (81% savings)
> 
> See [Cost Optimized Scenarios](#cost-optimized-scenarios) below for the optimized breakdowns.

## Pricing Overview

This guide provides cost estimates for running AI Trust OS at different scales. Prices are based on AWS us-east-1 region as of January 2024 and are subject to change.

## Quick Wins (Do These First)

Before deploying, implement these optimizations for immediate 80%+ savings:

1. **Model Routing** — Use Haiku for 80% of queries (10x cheaper than Sonnet)
2. **Telemetry Sampling** — Log 10% in production (90% CloudWatch savings)
3. **Right-Size Dev** — t3.small OpenSearch, 1 Kinesis shard, no replicas
4. **Disable in Dev** — Turn off Guardrails and human review workflows
5. **Use Serverless** — Neptune Serverless for variable dev workloads

## Cost Components

### 1. Bedrock Model Invocations

| Model | Input Tokens | Output Tokens |
|-------|--------------|---------------|
| Claude 3 Sonnet | $3.00 / 1M | $15.00 / 1M |
| Claude 3 Haiku | $0.25 / 1M | $1.25 / 1M |
| Titan Text Express | $0.80 / 1M | $1.60 / 1M |
| Llama 2 Chat | $0.75 / 1M | $1.00 / 1M |

### 2. Infrastructure Costs

#### VPC & Networking
| Component | Cost (Monthly) |
|-----------|----------------|
| NAT Gateway (x2) | $64.80 |
| VPC Endpoints (x5) | $35.00 |
| Data Transfer | Variable |

#### Neptune (Graph Database)
| Instance Type | Cost/Hour | Monthly (730 hrs) |
|---------------|-----------|-------------------|
| db.t3.medium | $0.098 | $71.54 |
| db.r6g.large | $0.365 | $266.45 |
| db.r6g.xlarge | $0.73 | $532.90 |
| db.r6g.2xlarge | $1.46 | $1,065.80 |

Storage: $0.12/GB-month + IOPS $0.023/IOPS-month

#### OpenSearch
| Instance Type | Cost/Hour | Monthly (730 hrs) |
|---------------|-----------|-------------------|
| t3.small | $0.036 | $26.28 |
| t3.medium | $0.072 | $52.56 |
| m6g.large | $0.128 | $93.44 |
| m6g.xlarge | $0.256 | $186.88 |
| r6g.large | $0.167 | $121.91 |

Storage (EBS gp3): $0.12/GB-month

#### Lambda
- Requests: $0.20 per 1M requests
- Compute: $0.0000166667 per GB-second
- Typical workload: $5-20/month

#### Kinesis Data Streams
- Shard Hour: $0.015
- PUT Payload Unit: $0.014 per million units
- Extended Retention: $0.020/GB-month

#### CloudWatch
- Logs Ingestion: $0.50/GB
- Logs Storage: $0.03/GB-month
- Dashboard: $3.00/dashboard/month
- Alarms: $0.10/alarm/month

## Scenario Estimates

### Scenario 1: Development Environment (10K requests/day)

**Assumptions:**
- 10,000 Bedrock invocations/day
- Average 2K input tokens, 500 output tokens per request
- Neptune: db.t3.medium (single instance)
- OpenSearch: 2x t3.small
- 2 Kinesis shards
- 30-day log retention

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (Claude 3 Haiku) | $135 |
| Neptune | $72 |
| OpenSearch | $53 |
| VPC (NAT + Endpoints) | $100 |
| Lambda | $10 |
| Kinesis | $45 |
| CloudWatch | $25 |
| KMS | $1 |
| **Total** | **~$441/month** |

### Scenario 2: Small Production (100K requests/day)

**Assumptions:**
- 100,000 Bedrock invocations/day
- Average 3K input tokens, 1K output tokens per request
- Neptune: db.r6g.large (cluster: 1 writer + 1 reader)
- OpenSearch: 2x m6g.large
- 4 Kinesis shards
- 90-day log retention
- Guardrails enabled

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (Claude 3 Sonnet) | $10,350 |
| Neptune | $533 |
| OpenSearch | $187 |
| VPC (NAT + Endpoints) | $100 |
| Lambda | $25 |
| Kinesis | $95 |
| CloudWatch | $75 |
| Guardrails | $500 |
| KMS | $1 |
| **Total** | **~$11,866/month** |

### Scenario 3: Large Production (1M requests/day)

**Assumptions:**
- 1,000,000 Bedrock invocations/day
- Average 4K input tokens, 1.5K output tokens per request
- Neptune: db.r6g.xlarge (cluster: 1 writer + 2 readers)
- OpenSearch: 3x r6g.xlarge + dedicated master
- 8 Kinesis shards
- 1-year log retention
- Guardrails enabled
- Cognito (10K users)
- WAF

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (Claude 3 Sonnet) | $138,000 |
| Neptune | $1,599 |
| OpenSearch | $560 |
| VPC (NAT + Endpoints) | $150 |
| Lambda | $100 |
| Kinesis | $200 |
| CloudWatch | $300 |
| Guardrails | $5,000 |
| Cognito | $250 |
| WAF | $150 |
| KMS | $1 |
| **Total** | **~$146,310/month** |

## Optimization Strategies

### 1. Neptune Cost Optimization

**Development:**
- Use db.t3.medium instead of r6g instances: **Save ~$450/month**
- Disable deletion protection (dev only): No cost, but risk
- Reduce backup retention to 1 day: **Save ~$20/month**

**Production:**
- Use read replicas only for read-heavy workloads
- Enable serverless for variable workloads
- Right-size instances based on actual metrics

### 2. OpenSearch Cost Optimization

```yaml
# Use UltraWarm for older data
UltraWarm:
  Enabled: true
  TransitionAfter: 7 days  # Move data older than 7 days
  
# Use Cold for archival
ColdStorage:
  Enabled: true
  TransitionAfter: 30 days
```

**Potential Savings:**
- UltraWarm vs. Hot: **60% cheaper**
- Cold vs. Hot: **90% cheaper**

### 3. Kinesis Cost Optimization

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| On-Demand Mode | For variable traffic | 30-50% |
| Batch PUTs | Combine records | 20-40% |
| Reduce Retention | 24h vs 7 days | 70% |

### 4. CloudWatch Cost Optimization

```python
# Sample logs instead of logging everything
import random

if random.random() < 0.1:  # 10% sampling
    logger.info("Bedrock invocation", extra=telemetry)
```

**Savings:** 90% reduction in log volume for high-throughput systems

### 5. Bedrock Cost Optimization

**Model Selection:**
| Use Case | Model | Cost vs Sonnet |
|----------|-------|----------------|
| Simple queries | Haiku | **10x cheaper** |
| Complex reasoning | Sonnet | Baseline |
| Coding tasks | Claude 3 Opus | 5x more expensive |

**Batch Processing:**
```python
# Use batch API for non-real-time workloads
bedrock_runtime.invoke_model(
    modelId="anthropic.claude-3-haiku",
    body=batch_payload  # Multiple requests in one call
)
```

## Reserved Capacity Pricing

### OpenSearch Reserved Instances

| Term | Payment | Discount vs On-Demand |
|------|---------|----------------------|
| 1-year | No Upfront | 31% |
| 1-year | Partial Upfront | 33% |
| 1-year | All Upfront | 35% |
| 3-year | All Upfront | 52% |

### Neptune Reserved Instances

| Term | db.r6g.large Discount |
|------|----------------------|
| 1-year | 20-30% |
| 3-year | 40-50% |

## Cost Monitoring

### Set Up Billing Alerts

```bash
# Create budget for monthly spend
aws budgets create-budget \
  --budget '{
    "BudgetName": "AI-Trust-OS-Monthly",
    "BudgetLimit": {
      "Amount": "12000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST",
    "CostFilters": {
      "TagKeyValue": [
        "Project$ai-trust-os"
      ]
    }
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "SNS",
      "Address": "arn:aws:sns:us-east-1:123456789012:billing-alerts"
    }]
  }]'
```

### Tag-Based Cost Allocation

All resources in AI Trust OS are tagged:
- `Project: ai-trust-os`
- `Environment: dev/staging/prod`
- `Pillar: discovery/telemetry/posture/proof`
- `CostCenter: <department>`

View costs by tag in AWS Cost Explorer:
```
Cost Explorer → Group by: Tag → Project
```

## Cost Calculator Script

```python
#!/usr/bin/env python3
"""
AI Trust OS Cost Calculator
"""

def calculate_costs(
    requests_per_day: int,
    input_tokens_per_request: int,
    output_tokens_per_request: int,
    model: str = "claude-3-sonnet",
    environment: str = "dev"
):
    """Calculate estimated monthly costs."""
    
    # Bedrock pricing per 1M tokens
    model_prices = {
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "titan-express": {"input": 0.80, "output": 1.60},
    }
    
    prices = model_prices.get(model, model_prices["claude-3-haiku"])
    
    # Calculate Bedrock costs
    monthly_requests = requests_per_day * 30
    input_tokens = monthly_requests * input_tokens_per_request / 1_000_000
    output_tokens = monthly_requests * output_tokens_per_request / 1_000_000
    
    bedrock_cost = (input_tokens * prices["input"]) + (output_tokens * prices["output"])
    
    # Infrastructure costs based on environment
    infra_costs = {
        "dev": {
            "neptune": 72,
            "opensearch": 53,
            "vpc": 100,
            "lambda": 10,
            "kinesis": 45,
            "cloudwatch": 25,
        },
        "prod": {
            "neptune": 533,
            "opensearch": 187,
            "vpc": 100,
            "lambda": 25,
            "kinesis": 95,
            "cloudwatch": 75,
        }
    }
    
    infra = infra_costs.get(environment, infra_costs["dev"])
    total_infra = sum(infra.values())
    
    return {
        "bedrock": bedrock_cost,
        "infrastructure": total_infra,
        "breakdown": infra,
        "total": bedrock_cost + total_infra
    }


# Example usage
if __name__ == "__main__":
    # 100K requests/day scenario
    costs = calculate_costs(
        requests_per_day=100_000,
        input_tokens_per_request=3000,
        output_tokens_per_request=1000,
        model="claude-3-sonnet",
        environment="prod"
    )
    
    print(f"Estimated Monthly Cost: ${costs['total']:,.2f}")
    print(f"  - Bedrock: ${costs['bedrock']:,.2f}")
    print(f"  - Infrastructure: ${costs['infrastructure']:,.2f}")
```

## Cost Optimized Scenarios

The following scenarios use the [cost-optimized.json](../config/cost-optimized.json) configuration with all optimizations enabled.

### Optimized Development (10K requests/day)

**Optimizations Applied:**
- Haiku-only (no model routing needed)
- t3.medium Neptune Serverless (min 2.5 NCU)
- t3.small OpenSearch (single instance)
- 1 Kinesis shard, 24h retention
- 7-day CloudWatch retention, 100% sampling
- Guardrails: DISABLED
- Human review: DISABLED

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (Claude 3 Haiku) | $18 |
| Neptune Serverless | ~$25 |
| OpenSearch | $26 |
| VPC (NAT + Endpoints) | $100 |
| Lambda | $5 |
| Kinesis | $12 |
| CloudWatch | $8 |
| KMS | $1 |
| **Total** | **~$75-120/month** |

**Savings vs Baseline:** 73-83%

### Optimized Small Production (100K requests/day)

**Optimizations Applied:**
- 80% Haiku / 20% Sonnet routing by complexity
- db.r5.large Neptune + 1 replica
- t3.medium OpenSearch × 2
- 2 Kinesis shards, 48h retention
- 30-day CloudWatch retention, 50% sampling
- Guardrails: ENABLED (content filters only)
- Human review: DISABLED

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (mixed routing) | ~$1,400 |
| Neptune | $533 |
| OpenSearch | $105 |
| VPC (NAT + Endpoints) | $100 |
| Lambda | $15 |
| Kinesis | $25 |
| CloudWatch | $35 |
| Guardrails | $150 |
| KMS | $1 |
| **Total** | **~$1,800-2,500/month** |

**Savings vs Baseline:** 79-85%

### Optimized Large Production (1M requests/day)

**Optimizations Applied:**
- Smart routing: 75% Haiku / 20% Sonnet / 5% Opus
- db.r6g.xlarge Neptune + 1 replica (reserved 1yr)
- r6g.large OpenSearch × 3 with UltraWarm
- 4 Kinesis shards, 7-day retention
- 1-year CloudWatch retention, 10% sampling
- ElastiCache for prompt/embedding cache
- Guardrails: FULL (with PII detection)
- Human review: ENABLED for sensitive content

| Component | Monthly Cost |
|-----------|--------------|
| Bedrock (smart routing) | ~$20,000 |
| Neptune (reserved) | $1,200 |
| OpenSearch (with UltraWarm) | $420 |
| VPC (NAT + Endpoints) | $150 |
| Lambda | $50 |
| Kinesis | $95 |
| CloudWatch | $60 |
| Guardrails | $750 |
| Cognito (10K users) | $250 |
| WAF | $150 |
| ElastiCache | $250 |
| KMS | $1 |
| **Total** | **~$28,000-35,000/month** |

**Savings vs Baseline:** 76-81%

## Summary

### Baseline Costs (Unoptimized)

| Scale | Requests/Day | Monthly Cost | Per 1K Requests |
|-------|--------------|--------------|-----------------|
| Dev | 10K | $441 | $1.47 |
| Small Prod | 100K | $11,866 | $3.95 |
| Large Prod | 1M | $146,310 | $4.88 |

### Optimized Costs (With cost-optimized.json)

| Scale | Requests/Day | Monthly Cost | Per 1K Requests | Savings |
|-------|--------------|--------------|-----------------|---------|
| Dev | 10K | **$75-120** | $0.25-0.40 | **73-83%** |
| Small Prod | 100K | **$1,800-2,500** | $0.60-0.83 | **79-85%** |
| Large Prod | 1M | **$28,000-35,000** | $0.93-1.17 | **76-81%** |

**Note:** Actual costs will vary based on:
- Token counts per request
- Chosen models
- Data transfer volumes
- Reserved capacity purchases
- Regional pricing differences