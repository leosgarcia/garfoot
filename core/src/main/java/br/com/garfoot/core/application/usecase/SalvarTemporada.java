package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.application.port.RepositorioTemporada;
import br.com.garfoot.core.model.campeonato.Campeonato;

import java.util.Objects;

public final class SalvarTemporada {
    private final RepositorioTemporada repositorio;

    public SalvarTemporada(RepositorioTemporada repositorio) {
        this.repositorio = Objects.requireNonNull(repositorio, "repositorio must not be null");
    }

    public void executar(Campeonato temporada) {
        repositorio.salvar(Objects.requireNonNull(temporada, "temporada must not be null"));
    }
}
