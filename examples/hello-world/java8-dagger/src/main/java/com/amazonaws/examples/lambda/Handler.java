package com.amazonaws.examples.lambda;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;

import com.amazonaws.examples.HelloWorld;
import com.amazonaws.examples.dagger.AppComponent;
import com.amazonaws.examples.dagger.DaggerAppComponent;

/**
 * Entrypoint
 */
public class Handler implements RequestHandler<Request,Response> {

    private final HelloWorld hello;
    private static boolean isWarm;

    public Handler() {
        AppComponent component = DaggerAppComponent.create();
        hello = component.hello();

    }

    @Override
    public Response handleRequest(Request request, Context context) {
        System.out.println("isWarm = " + isWarm);
        if (!isWarm) isWarm = true;

        System.out.println("value1 = " + request.key1);
        System.out.println("value2 = " + request.key2);
        System.out.println("value3 = " + request.key3);

        if (request.key1 != null) {
          hello.setMessage(request.key1);
        }

        return new Response(hello.getMessage());
    }
}
