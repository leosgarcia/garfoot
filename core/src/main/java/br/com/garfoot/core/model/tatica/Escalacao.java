package br.com.garfoot.core.model.tatica;

import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.StatusJogador;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

public record Escalacao(Formacao formacao, List<Jogador> titulares, List<Jogador> reservas) {
    public Escalacao {
        Objects.requireNonNull(formacao, "formacao must not be null");
        titulares = List.copyOf(Objects.requireNonNull(titulares, "titulares must not be null"));
        reservas = List.copyOf(Objects.requireNonNull(reservas, "reservas must not be null"));
        if (titulares.size() != 11) {
            throw new IllegalArgumentException("lineup must have exactly eleven starters");
        }

        Set<UUID> ids = new HashSet<>();
        for (Jogador jogador : concat(titulares, reservas)) {
            Objects.requireNonNull(jogador, "lineup player must not be null");
            if (!ids.add(jogador.id())) {
                throw new IllegalArgumentException("lineup must not contain duplicate players");
            }
            if (jogador.status() != StatusJogador.DISPONIVEL) {
                throw new IllegalArgumentException("injured or suspended players cannot be selected");
            }
        }
        for (int index = 0; index < titulares.size(); index++) {
            if (titulares.get(index).posicao() != formacao.posicoesTitulares().get(index)) {
                throw new IllegalArgumentException("starter position does not match formation slot " + index);
            }
        }
    }

    private static List<Jogador> concat(List<Jogador> titulares, List<Jogador> reservas) {
        return java.util.stream.Stream.concat(titulares.stream(), reservas.stream()).toList();
    }
}
