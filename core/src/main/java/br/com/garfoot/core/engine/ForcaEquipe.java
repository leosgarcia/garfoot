package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.jogador.RatingJogador;
import br.com.garfoot.core.model.jogador.Jogador;

import java.util.List;
import java.util.Objects;

public record ForcaEquipe(double ataque, double defesa) {
    public ForcaEquipe {
        validar(ataque, "ataque");
        validar(defesa, "defesa");
    }

    public static ForcaEquipe aPartirDe(List<RatingJogador> jogadores) {
        Objects.requireNonNull(jogadores, "jogadores must not be null");
        if (jogadores.isEmpty()) {
            throw new IllegalArgumentException("at least one player rating is required");
        }
        double ataque = jogadores.stream()
                .mapToDouble(rating -> rating.tecnica() * 0.30
                        + rating.finalizacao() * 0.40
                        + rating.passe() * 0.20
                        + rating.velocidade() * 0.10)
                .average()
                .orElseThrow();
        double defesa = jogadores.stream()
                .mapToDouble(rating -> rating.marcacao() * 0.50
                        + rating.fisico() * 0.30
                        + rating.mental() * 0.20)
                .average()
                .orElseThrow();
        return new ForcaEquipe(ataque, defesa);
    }

    public static ForcaEquipe aPartirDosJogadores(List<Jogador> jogadores) {
        Objects.requireNonNull(jogadores, "jogadores must not be null");
        return aPartirDe(jogadores.stream().map(jogador -> {
            var atributos = jogador.atributos();
            return new RatingJogador(atributos.tecnica(), atributos.fisico(), atributos.mental(),
                    atributos.velocidade(), atributos.finalizacao(), atributos.passe(),
                    atributos.marcacao(), atributos.potencial());
        }).toList());
    }

    private static void validar(double valor, String nome) {
        if (valor < 0 || valor > 100) {
            throw new IllegalArgumentException(nome + " must be between 0 and 100");
        }
    }
}
