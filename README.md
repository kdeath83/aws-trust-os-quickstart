# AI Trust OS Quick Start

## Overview

The **AI Trust OS Quick Start** is a production-ready infrastructure framework for governing AI workloads on AWS. Built on Amazon Bedrock, it provides comprehensive security, compliance, and observability for enterprise AI deployments.

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Trust OS Quick Start                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │  DISCOVERY  │  │  TELEMETRY  │  │   POSTURE   │            │
│   │             │  │             │  │             │            │
│   │ • Neptune   │  │ • OpenSearch│  │ • Guardrails│            │
│   │ • Config    │  │ • CloudWatch│  │ • Step Func │            │
│   │ • CodeGuru  │  │ • Kinesis   │  │ • Audit Mgr │            │
│   └─────────────┘  └─────────────┘  └─────────────┘            │
│                           │                                       │
│                    ┌─────────────┐                               │
│                    │    PROOF    │                               │
│                    │             │                               │
│                    │• PrivateLink│                               │
│                    │• KMS        │                               │
│                    │• Cognito    │                               │
│                    └─────────────┘                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### 🔍 **Pillar 1: Discovery**
- **Neptune Graph Database**: Track AI assets and their relationships
- **AWS Config**: Continuous compliance monitoring
- **CodeGuru**: Automated code scanning for AI SDK patterns
- **CloudTrail Integration**: Real-time asset discovery

### 📊 **Pillar 2: Telemetry**
- **OpenSearch**: Full-text search and analytics for AI telemetry
- **CloudWatch**: Real-time monitoring and alerting
- **Kinesis**: Real-time streaming of model invocations
- **Privacy-Preserving Logging**: Hash-based prompt/response tracking

### 🛡️ **Pillar 3: Posture**
- **Bedrock Guardrails**: Content filtering and safety policies
- **Step Functions**: Human review workflows for sensitive content
- **Audit Manager**: Compliance assessment and evidence collection
- **DynamoDB**: Review task management

### 🔒 **Pillar 4: Proof**
- **PrivateLink**: Private connectivity to AWS services
- **KMS**: Encryption for all data at rest and in transit
- **Cognito**: User authentication and authorization
- **API Gateway**: Controlled API access with private endpoints

## Quick Start

### Prerequisites

- AWS CLI v2+
- Python 3.11+
- AWS Account with Bedrock access
- IAM permissions to create CloudFormation stacks

### Deployment

```bash
# Clone the repository
git clone https://github.com/aws-samples/ai-trust-os-quickstart.git
cd ai-trust-os-quickstart

# Set environment
export ENVIRONMENT=dev
export AWS_REGION=us-east-1

# Deploy infrastructure
./deploy.sh --environment $ENVIRONMENT --region $AWS_REGION
```

See [Implementation Guide](docs/implementation-guide.md) for detailed deployment instructions.

## Architecture

![Architecture](docs/architecture-diagram.md)

The Quick Start deploys across four security pillars:

1. **Discovery** - Know what AI assets you have
2. **Telemetry** - Monitor how they're used
3. **Posture** - Control what they can do
4. **Proof** - Prove it's all secure

## Documentation

| Document | Description |
|----------|-------------|
| [Implementation Guide](docs/implementation-guide.md) | Step-by-step deployment instructions |
| [Architecture Diagram](docs/architecture-diagram.md) | System architecture and data flows |
| [Why Bedrock](docs/why-bedrock.md) | Comparison with OpenAI/Anthropic/Azure |
| [Cost Estimator](docs/cost-estimator.md) | Pricing for different scales |
| [Compliance Mapping](docs/compliance-mapping.md) | NIST AI RMF, ISO 42001, SOC2 alignment |

## Project Structure

```
ai-trust-os-quickstart/
├── templates/                    # CloudFormation templates
│   ├── ai-trust-os-main.yaml   # VPC, IAM, base networking
│   ├── pillar-1-discovery.yaml # CodeGuru, Config, Neptune
│   ├── pillar-2-telemetry.yaml # CloudWatch, OpenSearch, Kinesis
│   ├── pillar-3-posture.yaml   # Guardrails, Step Functions, Audit Manager
│   └── pillar-4-proof.yaml     # PrivateLink, KMS, Cognito
│
├── functions/                   # Lambda functions
│   ├── api-gateway-proxy/      # Capture API calls, log to OpenSearch
│   ├── guardrails-reviewer/    # Human review task management
│   ├── model-evaluation/       # Bedrock evaluation pipeline
│   └── agent-registry-sync/    # Neptune graph updates
│
├── docs/                        # Documentation
│   ├── implementation-guide.md
│   ├── architecture-diagram.md
│   ├── why-bedrock.md
│   ├── cost-estimator.md
│   └── compliance-mapping.md
│
├── config/                      # Configuration
│   └── quickstart-config.json
│
├── rules/                       # Governance rules
│   ├── codeguru-detectors/
│   └── config-rules/
│
└── README.md
```

## Cost Estimates

| Scale | Requests/Day | Monthly Cost |
|-------|--------------|--------------|
| Development | 10K | ~$441 |
| Small Production | 100K | ~$11,866 |
| Large Production | 1M | ~$146,310 |

See [Cost Estimator](docs/cost-estimator.md) for detailed breakdowns.

## Compliance

AI Trust OS maps to major compliance frameworks:

- ✅ **NIST AI Risk Management Framework** (AI RMF)
- ✅ **ISO/IEC 42001** - Artificial Intelligence Management System
- ✅ **SOC 2** - Trust Services Criteria
- ✅ **GDPR** - General Data Protection Regulation
- ✅ **CCPA** - California Consumer Privacy Act

See [Compliance Mapping](docs/compliance-mapping.md) for details.

## Security

### Defense in Depth

```
Layer 1: Network Isolation
  • VPC with private subnets
  • NAT Gateways for outbound
  • VPC Endpoints for AWS services

Layer 2: Identity & Access
  • Cognito User Pools
  • IAM with least privilege
  • MFA enforcement

Layer 3: Data Protection
  • KMS encryption
  • TLS 1.2+
  • S3 bucket policies

Layer 4: Application Security
  • Bedrock Guardrails
  • Human review workflows
  • Audit logging
```

## Supported AWS Regions

- us-east-1 (N. Virginia) - Full support
- us-west-2 (Oregon) - Full support
- eu-west-1 (Ireland) - Full support
- ap-southeast-2 (Sydney) - Full support
- ap-southeast-1 (Singapore) - Full support

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## Support

- **Issues**: [GitHub Issues](https://github.com/aws-samples/ai-trust-os-quickstart/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aws-samples/ai-trust-os-quickstart/discussions)
- **Documentation**: [Full Docs](docs/)

## Acknowledgments

- AWS Bedrock team for the foundational AI infrastructure
- AWS Security teams for compliance guidance
- AWS Solutions Architects for architecture review

---

**Built with ❤️ for the AWS AI Community**
