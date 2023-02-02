# AWS SAM JSON schema

## Context

The AWS SAM specification is spe

## Schema generation

At a high level, the final [`schema.json`](https://github.com/aws/serverless-application-model/blob/develop/samtranslator/schema/schema.json) is generated as such:

```mermaid
flowchart TD
  subgraph repogoformation["awslabs/goformation"]
    cfnschema(["CloudFormation schema"])
  end
  
  subgraph repocfndocs["awsdocs/aws-cloudformation-user-guide"]
    cfndocs(["CloudFormation documentation"])
  end

  subgraph reposamdocs["awsdocs/aws-sam-developer-guide"]
    samdocs(["SAM documentation"])
  end
  
  samschema(["SAM schema"])
  cfnschemadocs(["CloudFormation schema with documentation"])
  samschemadocs(["SAM schema with documentation"])
  final(["SAM and CloudFormation schema with documentation"])

  cfnschema --> cfnschemadocs
  cfndocs --> cfnschemadocs
  samschema --> samschemadocs
  samdocs --> samschemadocs
  cfnschemadocs --> final
  samschemadocs --> final
```
