package br.com.garfoot.core.model.campeonato;

import br.com.garfoot.core.model.partida.Partida;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class Rodada {
    private final int numero;
    private final List<Partida> partidas = new ArrayList<>();

    public Rodada(int numero) {
        if (numero < 1) {
            throw new IllegalArgumentException("numero must be positive");
        }
        this.numero = numero;
    }

    public int numero() {
        return numero;
    }

    public List<Partida> partidas() {
        return Collections.unmodifiableList(partidas);
    }

    public void adicionarPartida(Partida partida) {
        if (partida == null) {
            throw new NullPointerException("partida must not be null");
        }
        partidas.add(partida);
    }
}
