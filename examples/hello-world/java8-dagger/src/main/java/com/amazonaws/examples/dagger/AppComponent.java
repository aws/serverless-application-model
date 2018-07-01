package com.amazonaws.examples.dagger;

import javax.inject.Singleton;

import com.amazonaws.examples.HelloWorld;

import dagger.Component;

/**
 * Application DI component.
 */
@Singleton
@Component(modules = AppModule.class)
public interface AppComponent {
    HelloWorld hello();
}
