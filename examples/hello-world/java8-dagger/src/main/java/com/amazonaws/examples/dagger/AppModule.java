package com.amazonaws.examples.dagger;

import javax.inject.Singleton;

import com.amazonaws.examples.HelloWorld;

import dagger.Module;
import dagger.Provides;

/**
 * Application DI wiring.
 */
@Module
public class AppModule {

    @Provides
    @Singleton
    public HelloWorld helloModule() {
        return new HelloWorld();
    }
}
