---
title: Cloud Service Comparison
order: 50
---

The big cloud providers generally provide the same or comparable services under
different names.  I can't keep track of them all in my head, so this is a
running list of them that I add to as I look into more.

Microsoft maintains a [handy mapping between Azure and AWS services](https://learn.microsoft.com/en-us/azure/architecture/aws-professional/services).

## Core services

| Microsoft Azure       | Amazon Web Services   | Google Cloud
|-----------------------|-----------------------|------------------------
| Blob                  | S3                    | GCS

### Performance

These are the default limits on object storage services.  They all can be increased
on request.

Service              | Max Capacity | Read IOPS | Write IOPS | Read Bandwidth | Write Bandwidth | Source
---------------------|:------------:|:---------:|:----------:|:-----------:|:------------:|-------
Azure Blob           | 5 PiB        | 20,000    | 20,000     | 120 Gbit/s  | 60 Gbit/s    | [Azure storage account limits](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits#storage-limits)
AWS Simple Storage Service (S3) |  unlimited | 3,500 per prefix; unlimited prefixes | 5,500 per prefix; unlimited prefixes | unlimited, but 100 Gbit/s per VPC | unlimited, but 100 Gbit/s per VPC | [Optimizing Amazon S3 performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html); [Maximum transfer speed between Amazon EC2 and Amazon S3](https://aws.amazon.com/premiumsupport/knowledge-center/s3-maximum-transfer-speed-ec2/)
Google Cloud Storage | unlimited    | 5,000 + autoscale | 1,000 + autoscale | 200 Gbit/s  | 200 Gbit/s   | [Google Cloud Storage quotas and limits](https://cloud.google.com/storage/quotas)


## Serverless

| Microsoft Azure       | Amazon Web Services   | Google Cloud
|-----------------------|-----------------------|------------------------
| Azure Functions       | AWS Lambda            | Cloud Functions
| Azure Logic Apps      | AWS Step Functions    | Workflows

## Infrastructure

| Microsoft Azure       | Amazon Web Services   | Google Cloud
|-----------------------|-----------------------|------------------------
| ARM                   | CloudFormation        | Deployment Manager

## Other stuff

| Microsoft Azure       | Amazon Web Services   | Google Cloud
|-----------------------|-----------------------|------------------------
| Azure Orbital Ground Station | AWS Ground Station |
