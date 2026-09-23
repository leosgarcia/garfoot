package br.com.garfoot.core.model.jogador;

import java.util.Objects;

public record DadosRatingJogador(
        int idade,
        int alturaCm,
        long valorMercadoEur,
        int aparicoes,
        int minutosJogador,
        int gols,
        int assistencias,
        int internacionalCaps,
        Posicao posicao) {

    public DadosRatingJogador {
        if (idade < 15 || idade > 60) {
            throw new IllegalArgumentException("idade must be between 15 and 60");
        }
        if (alturaCm < 140 || alturaCm > 230) {
            throw new IllegalArgumentException("alturaCm must be between 140 and 230");
        }
        if (valorMercadoEur < 0 || aparicoes < 0 || minutosJogador < 0 || gols < 0
                || assistencias < 0 || internacionalCaps < 0) {
            throw new IllegalArgumentException("rating inputs must not be negative");
        }
        Objects.requireNonNull(posicao, "posicao must not be null");
    }
}
