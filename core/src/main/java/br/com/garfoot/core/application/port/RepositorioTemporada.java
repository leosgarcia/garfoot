package br.com.garfoot.core.application.port;

import br.com.garfoot.core.model.campeonato.Campeonato;

import java.util.Optional;
import java.util.UUID;

public interface RepositorioTemporada {
    void salvar(Campeonato temporada);
    Optional<Campeonato> carregar(UUID id);
}
