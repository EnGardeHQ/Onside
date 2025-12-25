terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    # Backend configuration should be provided via backend config file
    # Example: terraform init -backend-config=environments/production/backend.hcl
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "OnSide"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  name_prefix = "onside-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 3)

  common_tags = {
    Project     = "OnSide"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  cidr_block  = var.vpc_cidr
  azs         = local.azs
  environment = var.environment

  tags = local.common_tags
}

# Security Module
module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  environment = var.environment

  tags = local.common_tags
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  name_prefix          = local.name_prefix
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.database_subnet_ids
  security_group_id    = module.security.rds_security_group_id
  environment          = var.environment
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_allocated_storage
  database_name        = var.database_name
  master_username      = var.database_master_username
  multi_az             = var.rds_multi_az
  backup_retention     = var.rds_backup_retention_period

  tags = local.common_tags
}

# ElastiCache Redis Module
module "redis" {
  source = "./modules/redis"

  name_prefix       = local.name_prefix
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.cache_subnet_ids
  security_group_id = module.security.redis_security_group_id
  environment       = var.environment
  node_type         = var.redis_node_type
  num_cache_nodes   = var.redis_num_cache_nodes
  engine_version    = var.redis_engine_version

  tags = local.common_tags
}

# S3 Module (for object storage)
module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  environment = var.environment

  tags = local.common_tags
}

# ECS Cluster Module
module "ecs" {
  source = "./modules/ecs"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security.ecs_security_group_id]
  environment        = var.environment

  # Task configuration
  task_cpu    = var.ecs_task_cpu
  task_memory = var.ecs_task_memory
  desired_count = var.ecs_desired_count

  # Database and cache configuration
  database_url = "postgresql://${var.database_master_username}:${module.rds.master_password}@${module.rds.endpoint}/${var.database_name}"
  redis_url    = "redis://${module.redis.endpoint}:6379/0"

  # MinIO configuration (using S3 in production)
  minio_endpoint   = module.s3.bucket_regional_domain_name
  minio_access_key = var.minio_access_key
  minio_secret_key = var.minio_secret_key

  tags = local.common_tags

  depends_on = [
    module.rds,
    module.redis
  ]
}

# Application Load Balancer Module
module "alb" {
  source = "./modules/alb"

  name_prefix        = local.name_prefix
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  security_group_ids = [module.security.alb_security_group_id]
  environment        = var.environment
  certificate_arn    = var.acm_certificate_arn
  target_group_arn   = module.ecs.target_group_arn

  tags = local.common_tags
}

# CloudFront CDN Module
module "cloudfront" {
  source = "./modules/cloudfront"

  name_prefix        = local.name_prefix
  alb_domain_name    = module.alb.dns_name
  s3_bucket_id       = module.s3.bucket_id
  s3_bucket_domain   = module.s3.bucket_domain_name
  environment        = var.environment
  certificate_arn    = var.acm_certificate_arn

  tags = local.common_tags
}

# CloudWatch Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix   = local.name_prefix
  environment   = var.environment
  ecs_cluster   = module.ecs.cluster_name
  ecs_service   = module.ecs.service_name
  alb_arn       = module.alb.alb_arn
  rds_instance  = module.rds.instance_id
  redis_cluster = module.redis.cluster_id

  alarm_email = var.alarm_email

  tags = local.common_tags
}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
  environment = var.environment

  secrets = {
    database_url     = "postgresql://${var.database_master_username}:${module.rds.master_password}@${module.rds.endpoint}/${var.database_name}"
    redis_url        = "redis://${module.redis.endpoint}:6379/0"
    secret_key       = var.app_secret_key
    minio_access_key = var.minio_access_key
    minio_secret_key = var.minio_secret_key
  }

  tags = local.common_tags
}

# Auto Scaling Module
module "autoscaling" {
  source = "./modules/autoscaling"

  name_prefix        = local.name_prefix
  ecs_cluster_name   = module.ecs.cluster_name
  ecs_service_name   = module.ecs.service_name
  environment        = var.environment
  min_capacity       = var.autoscaling_min_capacity
  max_capacity       = var.autoscaling_max_capacity
  target_cpu_value   = var.autoscaling_target_cpu
  target_memory_value = var.autoscaling_target_memory

  tags = local.common_tags
}
