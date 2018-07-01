package com.amazonaws.examples;

import javax.inject.Inject;

public class HelloWorld {

    String msg;

    public HelloWorld() {
        this.msg = "Hello World";
    }

    public String getMessage() {
        return msg;
    }

    public void setMessage(String newMsg) {
        this.msg = newMsg;
    }

}
