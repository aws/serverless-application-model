from __future__ import print_function
import json


def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    notification_type = message['notificationType']
    handlers.get(notification_type, handle_unknown_type)(message)


def handle_bounce(message):
    message_id = message['mail']['messageId']
    bounced_recipients = message['bounce']['bouncedRecipients']
    addresses = list(
        recipient['emailAddress'] for recipient in bounced_recipients
    )
    bounce_type = message['bounce']['bounceType']
    print("Message %s bounced when sending to %s. Bounce type: %s" %
          (message_id, ", ".join(addresses), bounce_type))


def handle_complaint(message):
    message_id = message['mail']['messageId']
    complained_recipients = message['complaint']['complainedRecipients']
    addresses = list(
        recipient['emailAddress'] for recipient in complained_recipients
    )
    print("A complaint was reported by %s for message %s." %
          (", ".join(addresses), message_id))


def handle_delivery(message):
    message_id = message['mail']['messageId']
    delivery_timestamp = message['delivery']['timestamp']
    print("Message %s was delivered successfully at %s" %
          (message_id, delivery_timestamp))


def handle_unknown_type(message):
    print("Unknown message type:\n%s" % json.dumps(message))
    raise Exception("Invalid message type received: %s" %
                    message['notificationType'])


handlers = {"Bounce": handle_bounce,
            "Complaint": handle_complaint,
            "Delivery": handle_delivery}
