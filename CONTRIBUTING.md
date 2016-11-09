## Contribution Guidelines

Interested in contributing to the AWS Serverless Application Specification? Awesome! Read this document to understand how to report issues, contribute features and the participate in development process. We want to create a transparent and open process for evolving the AWS Serverless Application Specification. 

## Integrating AWS Serverless Application Specification into your tool
Are you building a new tool that will support AWS Serverless Application Specification? File an Issue and let us know what you are working on. We will support you however we can.

## Submitting feature requests
If you think of a cool feature that will greatly help hundreds of developers like you, we would love to hear about it. Follow these steps to submit your feature request:

1. Scan through the list of [Feature Requests](https://github.com/awslabs/serverless-application-specification/labels/feature-request). If you find your feature there, go +1 it. This is a good indication of interest from the community.
2. If don't find your feature in our backlog, create a new Issue and assign the `Feature Request` label to it.

Keep in mind that features in the specification should be driven by real use-cases. Answer the following questions in the issue you create:

- Does this feature simplify creating and deploying some aspect of a serverless application?
- Is this feature solving a problem faced by other serverless application developers?
- How do developers work around this problem today?
- How is the proposed feature better than the work around?

## Administrivia 

*Conversations*:

- Use GitHub Issues for conversation on specification design, feature requests, bugs etc.
- For more realtime conversations, use Gitter.

*Versioning and Branching*:

- As with the 2016-10-31 version, the **human readable** document is the source of truth.  If using a JSON Schema again to document the spec, it is secondary to the human documentation.  The documentation should live in a *.md file, in parallel to the 2016-10-31 document.
- The `master` branch shall remain the current, released AWS Serverless Application Specification (i.e. 2016-10-31).  We will work in a `development` branch for new features and merge them to `master` when they are ready.

*Labels*:  
Here are some labels we will use to keep Issues organized. Core contributors will add new labels as they see fit:
- `Feature Request`: Marks an issue as a feature request.
  - `Needs Documentation`: Used in conjuntion with Feature Request label to indicate that the feature needs documentation.
  - `Needs Tooling`: Used in conjunction with Feature Request label to indicate that feature needs tooling support in the transformation.
- `Bug`: Marks an issue as a bug.
