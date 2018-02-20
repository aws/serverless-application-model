def lambda_handler(event, context):
    class CustomException(Exception):
        pass

    raise CustomException('This is a custom error!')
