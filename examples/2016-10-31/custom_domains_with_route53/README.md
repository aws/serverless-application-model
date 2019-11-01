# Custom Domains support

Example SAM template for setting up Api Gateway resources for custom domains.

## Prerequisites for setting up custom domains
1. A domain name. You can purchase a domain name from a domain name provider.
1. A certificate ARN. Set up or import a valid certificate into AWS Certificate Manager. If the endpoint is EDGE, the certificate must be created in us-east-1.
1. A HostedZone in Route53 for the domain name.

## PostRequisites
After deploying the template, make sure you configure the DNS settings on the domain name provider's website. You will need to add Type A and Type AAAA DNS records that are point to ApiGateway's Hosted Zone Id. Read more [here](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-api-gateway.html)

## Running the example

```bash
$ sam deploy \
    --template-file /path_to_template/packaged-template.yaml \
    --stack-name my-new-stack \
    --capabilities CAPABILITY_IAM
```

Curl to the endpoint "http://example.com/home/fetch" should hit the Api.