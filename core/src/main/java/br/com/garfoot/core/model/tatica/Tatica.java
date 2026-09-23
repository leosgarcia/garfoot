package br.com.garfoot.core.model.tatica;

import java.util.Objects;

public record Tatica(Escalacao escalacao, EstiloJogo estilo) {
    public Tatica {
        Objects.requireNonNull(escalacao, "escalacao must not be null");
        Objects.requireNonNull(estilo, "estilo must not be null");
    }
}
