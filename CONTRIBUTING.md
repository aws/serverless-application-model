## Contribution Guidelines

Interested in contributing to the AWS Serverless Application Model (AWS SAM)?
Awesome! Read this document to understand how to report issues, contribute
features and the participate in development process. We want to create a
transparent and open process for evolving AWS SAM.

## Integrating AWS SAM into your tool
Are you building a new tool that will support AWS SAM? File an issue and let us
know what you are working on. We will support you however we can.

## Submitting feature requests
If you think of a cool feature that will greatly help hundreds of developers
like you, we would love to hear about it. Follow these steps to submit your
feature request:

1. Scan through the list
   of
   [feature requests](https://github.com/awslabs/serverless-application-specification/labels/feature-request).
   If you find your feature there, mark it +1. This is a good indication of
   interest from the community.
2. If you don't find your feature in our backlog, create a new issue and assign
   the `Feature Request` label to it.

Keep in mind that features should be driven by real use cases. Answer the
following questions in the issue that you create:

- Does this feature simplify creating and deploying some aspect of a Serverless
  application?
- Is this feature solving a problem faced by other Serverless application
  developers?
- How do developers work around this problem today?
- How is the proposed feature better than the work around?

## Adding features to AWS SAM

We welcome pull requests to add new features to AWS SAM. Take a look at the
backlog
of
[Feature Requests](https://github.com/awslabs/serverless-application-specification/labels/feature-request) and
pick an item that you find interesting. If the requirements have been
well-scoped, feel free to make the change and send a pull request.

Otherwise, start a conversation in the thread with your plan for implementing
the feature. When defining your feature, keep in mind that one of the core
tenets of AWS SAM is to keep it easy to use while allowing customers access to
use more advanced components, should they so choose. Here are some questions
that you should answer in your plan:

- **What is the problem you are solving?**  
	Example: Creating API endpoints require 24 steps, most of which are
    boilerplate and repetitive.

- **Describe persona of someone who is facing this problem? This will give you
    an understanding of how big of a problem it actually is.** Example: John
    just finished coding bootcamp and wants to create a Serverless app. He has
    basic coding skills and will be comfortable understanding infrastructure
    concepts, but probably be intimidated by the 24 steps required to create an
    API endpoint.

- **How do developers work around this problem today?**  
    Example: Manually click through every step on the website while refering to
    "How To" resources on the internet.

- **Describe your proposed solution?**  
    Example: We are creating a new AWS SAM resource called "API". Here is how it
    will look:

        Type: 'AWS::Serverless::Api'
        Properties:
            # Name of API endpoint
            Name: <string>
            # Path to their endpoint. Example: /hello
            Path: <string>
            # HTTP Method for their endpoint. Example: GET, POST etc
            Method: <string>


- **How is the proposed feature better than what the work around?**  
	Example: Developers can write a simple AWS SAM resource which will handle
    generating the boilerplate for them.

## Administrivia

*Conversations*:

- Use GitHub Issues for conversation on model design, feature requests, bugs
  etc.
- For more real-time conversations, use Gitter.

*Versioning and Branching*:

- As with the 2016-10-31 version, the **human readable** document is the source
  of truth. If using a JSON schema again to document the spec, it is secondary
  to the human documentation. The documentation should live in a *.md file, in
  parallel to the 2016-10-31 document.
- The `master` branch shall remain the current, released AWS SAM (i.e.
  2016-10-31). We will work in a `development` branch for new features and merge
  them to `master` when they are ready.

*Labels*:  
Here are some labels we will use to keep issues organized. Core contributors can
add new labels as they see fit:
- `Feature Request`: Marks an issue as a feature request.
  - `Needs Documentation`: Used in conjunction with the Feature Request label to
    indicate that the feature needs documentation.
  - `Needs Tooling`: Used in conjunction with the Feature Request label to
    indicate that feature needs tooling support in the transformation.
- `Bug`: Marks an issue as a bug.
