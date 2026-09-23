package br.com.garfoot.core;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertNotNull;

class CoreModuleTest {
    @Test
    void exposesTheCoreModule() {
        assertNotNull(CoreModule.class);
    }
}
