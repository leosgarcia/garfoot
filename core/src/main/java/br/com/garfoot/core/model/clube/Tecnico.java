package br.com.garfoot.core.model.clube;

import br.com.garfoot.core.util.DomainValidation;

import java.util.Objects;
import java.util.UUID;

public record Tecnico(UUID id, String nome) {
    public Tecnico {
        Objects.requireNonNull(id, "id must not be null");
        nome = DomainValidation.requireText(nome, "nome");
    }
}
