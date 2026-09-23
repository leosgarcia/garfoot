package br.com.garfoot.core.model.campeonato;

import br.com.garfoot.core.model.clube.Clube;

import java.util.Objects;

public record ClassificacaoItem(
        Clube clube, int pontos, int vitorias, int empates, int derrotas, int golsPro, int golsContra) {
    public ClassificacaoItem {
        Objects.requireNonNull(clube, "clube must not be null");
        if (pontos < 0 || vitorias < 0 || empates < 0 || derrotas < 0 || golsPro < 0 || golsContra < 0) {
            throw new IllegalArgumentException("classification statistics must not be negative");
        }
    }

    public int saldoGols() {
        return golsPro - golsContra;
    }
}
