package main

import (
        "fmt"
        "log"
        "context"
        "github.com/aws/aws-lambda-go/lambda"
)

type Event map[string]interface{}

func HandleRequest(ctx context.Context, event Event) (string, error) {
        log.Print("value1 = ", event["key1"] )
        log.Print("value2 = ", event["key2"] )
        log.Print("value3 = ", event["key3"] )

        return fmt.Sprintf("Hello World"), nil
}

func main() {
        lambda.Start(HandleRequest)
}
