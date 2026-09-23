package br.com.garfoot.core.util;

public final class DomainValidation {
    private DomainValidation() {
    }

    public static String requireText(String value, String fieldName) {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(fieldName + " must not be blank");
        }
        return value.trim();
    }

    public static int requireRange(int value, int minimum, int maximum, String fieldName) {
        if (value < minimum || value > maximum) {
            throw new IllegalArgumentException(fieldName + " must be between " + minimum + " and " + maximum);
        }
        return value;
    }
}
