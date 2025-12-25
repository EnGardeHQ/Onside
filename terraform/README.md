# OnSide Infrastructure as Code (Terraform)

This directory contains Terraform configurations for deploying the OnSide platform to AWS using Infrastructure as Code (IaC) principles.

## Architecture Overview

The infrastructure includes:

- **VPC**: Multi-AZ VPC with public, private, database, and cache subnets
- **ECS Fargate**: Container orchestration for the API and Celery workers
- **RDS PostgreSQL**: Managed database with Multi-AZ support in production
- **ElastiCache Redis**: Managed Redis for caching and Celery message broker
- **S3**: Object storage for files, reports, and static assets
- **ALB**: Application Load Balancer for traffic distribution
- **CloudFront**: CDN for global content delivery
- **CloudWatch**: Monitoring, logging, and alerting
- **Secrets Manager**: Secure secrets management
- **Auto Scaling**: Automatic scaling based on CPU/memory metrics

## Directory Structure

```
terraform/
├── main.tf                 # Main infrastructure configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── README.md              # This file
├── modules/               # Reusable Terraform modules
│   ├── vpc/              # VPC and networking
│   ├── security/         # Security groups and IAM roles
│   ├── rds/              # RDS PostgreSQL database
│   ├── redis/            # ElastiCache Redis
│   ├── s3/               # S3 buckets
│   ├── ecs/              # ECS cluster and services
│   ├── alb/              # Application Load Balancer
│   ├── cloudfront/       # CloudFront distribution
│   ├── monitoring/       # CloudWatch dashboards and alarms
│   ├── secrets/          # AWS Secrets Manager
│   └── autoscaling/      # Auto Scaling policies
└── environments/          # Environment-specific configurations
    ├── dev/
    ├── staging/
    └── production/
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
   ```bash
   aws configure
   ```

2. **Terraform** installed (version >= 1.5.0)
   ```bash
   terraform version
   ```

3. **S3 Backend** for Terraform state (create manually or use provided script)
   ```bash
   aws s3 mb s3://onside-terraform-state-<account-id>
   aws dynamodb create-table \
     --table-name onside-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

## Deployment Instructions

### Development Environment

1. Navigate to the development environment:
   ```bash
   cd environments/dev
   ```

2. Initialize Terraform:
   ```bash
   terraform init -backend-config=backend.hcl
   ```

3. Review the execution plan:
   ```bash
   terraform plan -var-file=terraform.tfvars
   ```

4. Apply the configuration:
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

### Staging Environment

```bash
cd environments/staging
terraform init -backend-config=backend.hcl
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### Production Environment

Production deployments require additional approval:

```bash
cd environments/production
terraform init -backend-config=backend.hcl
terraform plan -var-file=terraform.tfvars
# Review the plan carefully
terraform apply -var-file=terraform.tfvars
```

## Configuration

### Environment Variables

Create a `terraform.tfvars` file in each environment directory:

```hcl
# Environment configuration
environment = "production"
aws_region  = "us-east-1"

# VPC configuration
vpc_cidr = "10.0.0.0/16"

# RDS configuration
rds_instance_class         = "db.t3.small"
rds_allocated_storage      = 100
rds_multi_az               = true
rds_backup_retention_period = 30

# Redis configuration
redis_node_type      = "cache.t3.small"
redis_num_cache_nodes = 2

# ECS configuration
ecs_task_cpu     = "1024"
ecs_task_memory  = "2048"
ecs_desired_count = 4

# Auto Scaling configuration
autoscaling_min_capacity  = 2
autoscaling_max_capacity  = 20
autoscaling_target_cpu    = 70
autoscaling_target_memory = 80

# Domain and SSL
domain_name         = "app.onside.com"
acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxx"

# Secrets (use environment variables or secrets manager)
app_secret_key    = "your-secret-key-here"
minio_access_key  = "your-access-key"
minio_secret_key  = "your-secret-key"
alarm_email       = "alerts@onside.com"
```

### Backend Configuration

Create a `backend.hcl` file in each environment:

```hcl
bucket         = "onside-terraform-state-<account-id>"
key            = "onside/production/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "onside-terraform-locks"
encrypt        = true
```

## Modules

### VPC Module
Creates a multi-AZ VPC with:
- Public subnets for ALB
- Private subnets for ECS tasks
- Database subnets for RDS
- Cache subnets for ElastiCache
- NAT Gateways for outbound internet access
- VPC Flow Logs for network monitoring

### ECS Module
Deploys containerized applications:
- ECS Fargate cluster
- Task definitions for API and Celery workers
- ECS services with auto-scaling
- CloudWatch log groups

### RDS Module
Managed PostgreSQL database:
- Multi-AZ deployment in production
- Automated backups
- Enhanced monitoring
- Encryption at rest

### Redis Module
ElastiCache Redis cluster:
- Multi-node setup for high availability
- Automatic failover
- Encryption in transit

### Monitoring Module
CloudWatch monitoring:
- Custom dashboards
- CloudWatch alarms for critical metrics
- SNS topics for notifications
- Log aggregation

## Security

### Secrets Management

Sensitive values should NEVER be committed to version control:

1. Use environment variables:
   ```bash
   export TF_VAR_app_secret_key="your-secret"
   ```

2. Use AWS Secrets Manager (recommended):
   ```bash
   aws secretsmanager create-secret \
     --name onside/production/app-secrets \
     --secret-string '{"app_secret_key":"xxx"}'
   ```

3. Use `.tfvars` files (add to .gitignore):
   ```bash
   echo "*.tfvars" >> .gitignore
   ```

### Security Best Practices

- All data encrypted at rest and in transit
- Security groups follow principle of least privilege
- IAM roles with minimal required permissions
- VPC endpoints for AWS services
- WAF rules for ALB protection
- Regular security scanning with AWS Security Hub

## Cost Optimization

### Development Environment
- Single NAT Gateway
- Single AZ deployment
- Smaller instance sizes
- Reduced backup retention
- Auto-shutdown during off-hours

### Production Environment
- Multi-AZ for high availability
- Reserved instances for predictable workloads
- S3 lifecycle policies for log archival
- CloudWatch log retention policies
- Auto-scaling to match demand

## Disaster Recovery

### Backup Strategy

1. **RDS**: Automated daily backups with 30-day retention
2. **S3**: Versioning enabled with lifecycle policies
3. **Infrastructure**: Terraform state stored in S3 with versioning

### Recovery Procedures

1. Database recovery from RDS snapshot
2. Infrastructure recreation from Terraform state
3. Application deployment via CI/CD pipeline

## Monitoring and Alerting

### CloudWatch Dashboards

- API performance metrics
- Database performance
- Redis cache metrics
- ECS task health
- ALB request metrics

### Alarms

- High CPU/Memory utilization
- Database connection errors
- ECS task failures
- ALB unhealthy targets
- High error rates

## Maintenance

### Updating Infrastructure

1. Make changes to Terraform files
2. Run `terraform plan` to review changes
3. Run `terraform apply` to apply changes
4. Monitor CloudWatch for any issues

### Database Migrations

Database migrations should be run separately:
```bash
aws ecs run-task \
  --cluster onside-production \
  --task-definition onside-api \
  --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"api","command":["alembic","upgrade","head"]}]}'
```

## Troubleshooting

### Common Issues

1. **Terraform state locked**
   ```bash
   terraform force-unlock <lock-id>
   ```

2. **ECS task failing to start**
   ```bash
   aws ecs describe-tasks --cluster <cluster> --tasks <task-id>
   aws logs tail /ecs/onside-api --follow
   ```

3. **Database connection issues**
   - Check security group rules
   - Verify credentials in Secrets Manager
   - Check RDS instance status

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/intro.html)

## Support

For infrastructure issues:
- Create an issue in the repository
- Contact the DevOps team
- Check CloudWatch logs for application errors
