# Design decisions

Document design decisions here.

## CloudWatchLogs Event Source

### LogGroupName

For now we have decided `LogGroupName` should be a required property for simplicity. A future enhancement could make this optional and create a new CloudWatch Log Group when not provided. Users could `Ref` the resource if we exposed/documented the resource naming convention.

### FilterPattern

Decided `FilterPattern` should be a required property so as not to provide a footgun to users. If this were to default to `""`, noisy logs could invoke hundreds/thousands of Lambda functions in short periods of time.