package br.com.garfoot.core.model.tatica;

import br.com.garfoot.core.model.jogador.Posicao;

import java.util.List;
import java.util.Objects;

/** Formation represented by the exact positions required for its eleven starters. */
public record Formacao(String nome, List<Posicao> posicoesTitulares) {
    public Formacao {
        if (nome == null || nome.isBlank()) {
            throw new IllegalArgumentException("nome must not be blank");
        }
        posicoesTitulares = List.copyOf(Objects.requireNonNull(posicoesTitulares, "posicoesTitulares"));
        if (posicoesTitulares.size() != 11 || posicoesTitulares.stream().anyMatch(Objects::isNull)) {
            throw new IllegalArgumentException("formation must define exactly eleven positions");
        }
        if (posicoesTitulares.stream().filter(posicao -> posicao == Posicao.GOL).count() != 1) {
            throw new IllegalArgumentException("formation must define exactly one goalkeeper");
        }
    }

    public static Formacao quatroQuatroDois() {
        return new Formacao("4-4-2", List.of(
                Posicao.GOL, Posicao.LAT, Posicao.ZAG, Posicao.ZAG, Posicao.LAT,
                Posicao.VOL, Posicao.MEI, Posicao.MEI, Posicao.VOL,
                Posicao.ATA, Posicao.ATA));
    }
}
