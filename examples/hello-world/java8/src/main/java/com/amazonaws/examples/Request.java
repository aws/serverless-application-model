package com.amazonaws.examples;

public class Request {
    String key1;
    String key2;
    String key3;

    public String getKey1() {
        return key1;
    }

    public void setKey1(String key1) {
        this.key1 = key1;
    }

    public String getKey2() {
        return key2;
    }

    public void setKey2(String key2) {
        this.key2 = key2;
    }

    public String getKey3() {
        return key3;
    }

    public void setKey3(String key3) {
        this.key3 = key3;
    }

    public Request(String key1, String key2, String key3) {
        this.key1 = key1;
        this.key2 = key2;
        this.key3 = key3;
    }

    public Request() {}
}
