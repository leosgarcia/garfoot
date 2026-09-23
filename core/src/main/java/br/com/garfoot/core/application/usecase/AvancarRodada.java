package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.engine.ForcaEquipe;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.partida.Partida;

import java.util.Objects;
import java.util.function.Function;

public final class AvancarRodada {
    private static final long INCREMENTO_SEED = 0x9E3779B97F4A7C15L;
    private final SimularPartida simularPartida;
    private final Function<Clube, ForcaEquipe> resolverForca;

    public AvancarRodada(SimularPartida simularPartida, Function<Clube, ForcaEquipe> resolverForca) {
        this.simularPartida = Objects.requireNonNull(simularPartida, "simularPartida must not be null");
        this.resolverForca = Objects.requireNonNull(resolverForca, "resolverForca must not be null");
    }

    public Rodada executar(Rodada rodada, long seed) {
        Objects.requireNonNull(rodada, "rodada must not be null");
        long indice = 0;
        for (Partida partida : rodada.partidas()) {
            if (partida.status() == br.com.garfoot.core.model.partida.StatusPartida.AGENDADA) {
                simularPartida.executar(partida, resolverForca.apply(partida.mandante()),
                        resolverForca.apply(partida.visitante()), seed + indice * INCREMENTO_SEED);
            }
            indice++;
        }
        return rodada;
    }
}
