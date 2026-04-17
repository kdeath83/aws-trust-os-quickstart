# AI Trust OS - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI Trust OS Architecture                                    │
│                                                                                          │
│   ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│   │                               Pillar 1: Discovery                                 │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐  │   │
│   │  │   CodeGuru   │  │   Config     │  │   Neptune    │  │   CloudTrail        │  │   │
│   │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌───────────────┐  │  │   │
│   │  │  │Reviewer│  │  │  │  Rules │  │  │  │  Graph │  │  │  │   Events      │  │  │   │
│   │  │  │Scanner │  │  │  │  Eval  │  │  │  │   DB   │  │  │  │   Parser      │  │  │   │
│   │  │  └───┬────┘  │  │  └───┬────┘  │  │  └───┬────┘  │  │  │       │       │  │  │   │
│   │  │      │       │  │      │       │  │      │       │  │  │       │       │  │  │   │
│   │  │  [AI SDK      │  │  [Compliance│  │  │  [Asset    │  │  │       ▼       │  │  │   │
│   │  │   Detection]  │  │   Checks]   │  │  │  Registry] │  │  │  ┌───────────┐ │  │  │   │
│   │  │               │  │               │  │  │            │  │  │  │ Lambda    │ │  │  │   │
│   │  └───────────────┘  │               │  │  │            │  │  │  │ Registry  │ │  │  │   │
│   │                     │               │  │  │            │  │  │  │   Sync    │ │  │  │   │
│   │                     └───────────────┘  │  │            │  │  │  └─────┬─────┘ │  │  │   │
│   │                                        │  │            │  │  │        │       │  │  │   │
│   │                                        │  └─────┬──────┘  │  └────────┼───────┘  │  │   │
│   │                                        │        │         │           │          │  │   │
│   │                                        │        │         └───────────┼──────────┘  │   │
│   │                                        │        │                     │             │   │
│   └────────────────────────────────────────┼────────┼─────────────────────┼─────────────┘   │
│                                            │        │                     │                 │
│   ┌────────────────────────────────────────┼────────┼─────────────────────┼─────────────┐   │
│   │                              Pillar 2: Telemetry                                │   │
│   │  ┌─────────────────────────────────┐   │        │                     │             │   │
│   │  │         OpenSearch              │   │        │                     │             │   │
│   │  │  ┌─────────┐  ┌─────────────┐  │   │        │                     │             │   │
│   │  │  │ Indices │  │   Kibana    │  │   │        │                     │             │   │
│   │  │  │ • invoc │  │  Dashboard  │  │   │        │                     │             │   │
│   │  │  │ • audit │  │             │  │   │        │                     │             │   │
│   │  │  │ • error │  │ [Analytics] │  │   │        │                     │             │   │
│   │  │  └────┬────┘  └─────────────┘  │   │        │                     │             │   │
│   │  │       │                         │   │        │                     │             │   │
│   │  │  [Aggregated Logs]              │   │        │                     │             │   │
│   │  └───────┼─────────────────────────┘   │        │                     │             │   │
│   │          │                              │        │                     │             │   │
│   │  ┌───────┴───────────┐                  │        │                     │             │   │
│   │  │  CloudWatch Logs  │                  │        │                     │             │   │
│   │  │  ┌─────────────┐  │                  │        │                     │             │   │
│   │  │  │ /aws/lambda │  │                  │        │                     │             │   │
│   │  │  │ /aws/bedrock│  │                  │        │                     │             │   │
│   │  │  │ /ai-trust   │  │                  │        │                     │             │   │
│   │  │  └──────┬──────┘  │                  │        │                     │             │   │
│   │  │         │         │                  │        │                     │             │   │
│   │  │  [Real-time Logs] │                  │        │                     │             │   │
│   │  └─────────┼─────────┘                  │        │                     │             │   │
│   │            │                            │        │                     │             │   │
│   │  ┌─────────┴──────────┐                 │        │                     │             │   │
│   │  │   Kinesis Data     │                 │        │                     │             │   │
│   │  │     Stream         │                 │        │                     │             │   │
│   │  │  ┌──────────────┐  │                 │        │                     │             │   │
│   │  │  │ Real-time    │  │                 │        │                     │             │   │
│   │  │  │ Streaming    │  │                 │        │                     │             │   │
│   │  │  └──────────────┘  │                 │        │                     │             │   │
│   │  └────────────────────┘                 │        │                     │             │   │
│   │                                         │        │                     │             │   │
│   └─────────────────────────────────────────┼────────┼─────────────────────┼─────────────┘   │
│                                             │        │                     │                 │
│   ┌─────────────────────────────────────────┼────────┼─────────────────────┼─────────────┐   │
│   │                              Pillar 3: Posture                                    │   │
│   │  ┌─────────────────┐                      │        │                     │             │   │
│   │  │  Bedrock        │                      │        │                     │             │   │
│   │  │  Guardrails     │                      │        │                     │             │   │
│   │  │  ┌───────────┐  │                      │        │                     │             │   │
│   │  │  │ Content   │  │                      │        │                     │             │   │
│   │  │  │ Filter    │  │                      │        │                     │             │   │
│   │  │  │ PII       │  │                      │        │                     │             │   │
│   │  │  │ Topics    │  │                      │        │                     │             │   │
│   │  │  └─────┬─────┘  │                      │        │                     │             │   │
│   │  │        │        │                      │        │                     │             │   │
│   │  │  [Policy Enforcement]                  │        │                     │             │   │
│   │  └────────┼────────┘                      │        │                     │             │   │
│   │           │                               │        │                     │             │   │
│   │  ┌────────┴────────────────────┐          │        │                     │             │   │
│   │  │    Step Functions           │          │        │                     │             │   │
│   │  │  ┌───────────────────────┐  │          │        │                     │             │   │
│   │  │  │ Human Review Workflow │  │          │        │                     │             │   │
│   │  │  │  • Evaluate          │  │          │        │                     │             │   │
│   │  │  │  • Request Review    │  │          │        │                     │             │   │
│   │  │  │  • Wait              │  │          │        │                     │             │   │
│   │  │  │  • Approve/Block     │  │          │        │                     │             │   │
│   │  │  └───────────────────────┘  │          │        │                     │             │   │
│   │  └───────────────────────────┘          │        │                     │             │   │
│   │                                           │        │                     │             │   │
│   │  ┌──────────────────────────┐           │        │                     │             │   │
│   │  │  Audit Manager           │           │        │                     │             │   │
│   │  │  [Compliance Evidence]   │           │        │                     │             │   │
│   │  └──────────────────────────┘           │        │                     │             │   │
│   │                                           │        │                     │             │   │
│   └───────────────────────────────────────────┼────────┼─────────────────────┼─────────────┘   │
│                                               │        │                     │                 │
│   ┌───────────────────────────────────────────┼────────┼─────────────────────┼─────────────┐   │
│   │                              Pillar 4: Proof                                      │   │
│   │  ┌─────────────────────────────────────────┐       │                     │             │   │
│   │  │      VPC PrivateLink Endpoints          │       │                     │             │   │
│   │  │  ┌────────┐ ┌────────┐ ┌────────┐      │       │                     │             │   │
│   │  │  │Bedrock │ │KMS     │ │Cloud   │      │       │                     │             │   │
│   │  │  │Runtime │ │        │ │Watch   │      │       │                     │             │   │
│   │  │  └────────┘ └────────┘ └────────┘      │       │                     │             │   │
│   │  │  [Private Connectivity - No Internet]    │       │                     │             │   │
│   │  └─────────────────────────────────────────┘       │                     │             │   │
│   │                                                    │                     │             │   │
│   │  ┌─────────────────────────────────────────┐       │                     │             │   │
│   │  │      Amazon Cognito                    │       │                     │             │   │
│   │  │  ┌───────────────────────────────┐    │       │                     │             │   │
│   │  │  │ User Pool  •  Identity Pool   │    │       │                     │             │   │
│   │  │  │ MFA  •  OAuth 2.0  •  JWT     │    │       │                     │             │   │
│   │  │  └───────────────────────────────┘    │       │                     │             │   │
│   │  │  [Authentication & Authorization]      │       │                     │             │   │
│   │  └─────────────────────────────────────────┘       │                     │             │   │
│   │                                                    │                     │             │   │
│   │  ┌─────────────────────────────────────────┐       │                     │             │   │
│   │  │      API Gateway (Private)             │       │                     │             │   │
│   │  │  ┌───────────────────────────────┐    │       │                     │             │   │
│   │  │  │ /bedrock/invoke-model         │    │       │                     │             │   │
│   │  │  │ /telemetry/query              │    │       │                     │             │   │
│   │  │  │ /guardrails/review            │    │       │                     │             │   │
│   │  │  └───────────────────────────────┘    │       │                     │             │   │
│   │  │  [Controlled API Access]               │       │                     │             │   │
│   │  └─────────────────────────────────────────┘       │                     │             │   │
│   │                                                    │                     │             │   │
│   └────────────────────────────────────────────────────┼─────────────────────┼─────────────┘   │
│                                                        │                     │                 │
│   ┌────────────────────────────────────────────────────┴─────────────────────┴─────────────┐   │
│   │                                     AWS KMS                                             │   │
│   │                     [Encryption for all data at rest and in transit]                     │   │
│   │                                                                                         │   │
│   │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │   │
│   │  │ Neptune DB    │  │ OpenSearch    │  │ S3 Buckets    │  │ CloudWatch    │           │   │
│   │  │ Encrypted     │  │ Encrypted     │  │ Encrypted     │  │ Logs Encrypted│           │   │
│   │  └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘           │   │
│   │                                                                                         │   │
│   └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Bedrock Model Invocation Flow

```
┌──────────┐    ┌──────────────────┐    ┌───────────────┐    ┌───────────────┐
│  Client  │───▶│  API Gateway     │───▶│  Lambda Proxy   │───▶│  Bedrock      │
│  (App)   │    │  (Private VPC)   │    │  + Guardrails │    │  Runtime      │
└──────────┘    └──────────────────┘    └───────┬───────┘    └───────────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │  CloudWatch Logs │
                                      │  (Real-time)     │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │  OpenSearch      │
                                      │  (Analytics)     │
                                      └──────────────────┘
```

### 2. Human Review Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Guardrail    │────▶│  Step         │────▶│  DynamoDB     │
│  Intervention │     │  Functions    │     │  (Review      │
└───────────────┘     │  Workflow     │     │  Tasks)       │
                      └───────┬───────┘     └───────┬───────┘
                              │                     │
                              ▼                     ▼
                      ┌───────────────┐     ┌───────────────┐
                      │  SNS          │     │  Human        │
                      │  (Alert)      │     │  Reviewer     │
                      └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │  Decision     │
                                            │  Recorded     │
                                            └───────────────┘
```

### 3. Asset Discovery Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  CloudTrail   │────▶│  Lambda       │────▶│  Neptune      │
│  (Events)     │     │  (Parse)      │     │  (Graph DB)   │
└───────────────┘     └───────────────┘     └───────┬───────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │  Gremlin      │
                                            │  Queries      │
                                            └───────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Isolation                                  │
│  • VPC with private subnets                                  │
│  • NAT Gateways for outbound                                 │
│  • VPC Endpoints for AWS services                            │
│  • Security Groups with least privilege                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Identity & Access                                   │
│  • Cognito User Pools for authentication                   │
│  • IAM roles with service-linked policies                  │
│  • VPC endpoint policies                                    │
│  • API Gateway resource policies                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Data Protection                                     │
│  • KMS encryption for all data stores                      │
│  • TLS 1.2+ for all transit                                  │
│  • S3 bucket policies with encryption enforcement          │
│  • CloudWatch Logs encryption                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Application Security                                │
│  • Bedrock Guardrails for content filtering                │
│  • Human review for sensitive decisions                    │
│  • Audit logging for all API calls                        │
│  • AWS Config for compliance monitoring                    │
└─────────────────────────────────────────────────────────────┘
```

## Component Interactions

| Component | Interacts With | Purpose |
|-----------|---------------|---------|
| Lambda Proxy | Bedrock, OpenSearch, S3 | Capture and log model invocations |
| Guardrails | Step Functions, SNS | Filter content and trigger review |
| Neptune | CloudTrail, Lambda | Build asset relationship graph |
| OpenSearch | CloudWatch, Lambda | Store and query telemetry |
| Kinesis | Firehose, S3 | Stream real-time events |
| Cognito | API Gateway, IAM | Authenticate API requests |
| KMS | All data stores | Encrypt data at rest |

## Scaling Considerations

### Horizontal Scaling
- **OpenSearch**: Add nodes for read scaling
- **Neptune**: Read replicas for query scaling
- **Lambda**: Automatic scaling based on concurrency
- **Kinesis**: Shard splitting for throughput

### Vertical Scaling
- **OpenSearch**: Upgrade instance types
- **Neptune**: Resize instances (maintenance window required)
- **Config**: Adjust recorder frequency

### Regional Deployment
```
┌─────────────────────────────────────────────────────────────┐
│                     Multi-Region Deployment                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐         ┌─────────────┐                │
│   │  us-east-1  │         │  eu-west-1  │                │
│   │             │◄───────►│             │                │
│   │ Primary     │  VPC    │ Secondary   │                │
│   │ Region      │  Peering│ Region      │                │
│   │             │         │             │                │
│   │ • Neptune   │         │ • Neptune   │                │
│   │ • OpenSearch│         │ • OpenSearch│                │
│   │ • Bedrock   │         │ • Bedrock   │                │
│   └─────────────┘         └─────────────┘                │
│                                                             │
│   [Cross-region replication via S3 + EventBridge]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```