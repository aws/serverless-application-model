package com.amazonaws.examples;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;

public class HelloWorld implements RequestHandler<Request, Response> {
    public Response handleRequest(Request request, Context context) {
        System.out.println("value1 = " + request.key1);
        System.out.println("value2 = " + request.key2);
        System.out.println("value3 = " + request.key3);

        return new Response("Hello World");
    }
}
