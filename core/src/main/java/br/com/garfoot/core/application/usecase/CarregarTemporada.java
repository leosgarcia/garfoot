package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.application.port.RepositorioTemporada;
import br.com.garfoot.core.model.campeonato.Campeonato;

import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

public final class CarregarTemporada {
    private final RepositorioTemporada repositorio;

    public CarregarTemporada(RepositorioTemporada repositorio) {
        this.repositorio = Objects.requireNonNull(repositorio, "repositorio must not be null");
    }

    public Campeonato executar(UUID id) {
        return executarSeExistir(id)
                .orElseThrow(() -> new IllegalArgumentException("season not found: " + id));
    }

    public Optional<Campeonato> executarSeExistir(UUID id) {
        return repositorio.carregar(Objects.requireNonNull(id, "id must not be null"));
    }
}
