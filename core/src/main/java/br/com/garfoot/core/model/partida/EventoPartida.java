package br.com.garfoot.core.model.partida;

import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.util.DomainValidation;

import java.util.Objects;
import java.util.Optional;

public record EventoPartida(
        int minuto,
        TipoEvento tipo,
        Jogador jogadorEnvolvido,
        String descricaoNarrativa,
        Jogador jogadorQueSai,
        Jogador jogadorQueEntra) {
    public EventoPartida(int minuto, TipoEvento tipo, Jogador jogadorEnvolvido, String descricaoNarrativa) {
        this(minuto, tipo, jogadorEnvolvido, descricaoNarrativa, null, null);
    }

    public EventoPartida {
        DomainValidation.requireRange(minuto, 0, 120, "minuto");
        Objects.requireNonNull(tipo, "tipo must not be null");
        descricaoNarrativa = DomainValidation.requireText(descricaoNarrativa, "descricaoNarrativa");
        if (tipo == TipoEvento.SUBSTITUICAO && (jogadorQueSai == null) != (jogadorQueEntra == null)) {
            throw new IllegalArgumentException("substitution must identify both players or neither");
        }
        if (tipo == TipoEvento.SUBSTITUICAO && jogadorQueSai != null) {
            if (jogadorEnvolvido == null || !jogadorEnvolvido.id().equals(jogadorQueSai.id())) {
                throw new IllegalArgumentException("jogadorEnvolvido must be the player leaving");
            }
            if (jogadorQueSai.id().equals(jogadorQueEntra.id())) {
                throw new IllegalArgumentException("substitution players must be different");
            }
        }
        if (tipo != TipoEvento.SUBSTITUICAO && (jogadorQueSai != null || jogadorQueEntra != null)) {
            throw new IllegalArgumentException("only substitutions can identify players entering or leaving");
        }
    }

    public Optional<Jogador> jogador() {
        return Optional.ofNullable(jogadorEnvolvido);
    }

    public Optional<Jogador> jogadorSai() {
        return Optional.ofNullable(jogadorQueSai);
    }

    public Optional<Jogador> jogadorEntra() {
        return Optional.ofNullable(jogadorQueEntra);
    }
}
