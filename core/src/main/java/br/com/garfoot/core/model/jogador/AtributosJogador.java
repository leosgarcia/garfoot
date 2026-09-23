package br.com.garfoot.core.model.jogador;

import br.com.garfoot.core.util.DomainValidation;

public record AtributosJogador(
        int tecnica,
        int fisico,
        int mental,
        int velocidade,
        int finalizacao,
        int passe,
        int marcacao,
        int potencial) {

    public AtributosJogador {
        tecnica = DomainValidation.requireRange(tecnica, 0, 100, "tecnica");
        fisico = DomainValidation.requireRange(fisico, 0, 100, "fisico");
        mental = DomainValidation.requireRange(mental, 0, 100, "mental");
        velocidade = DomainValidation.requireRange(velocidade, 0, 100, "velocidade");
        finalizacao = DomainValidation.requireRange(finalizacao, 0, 100, "finalizacao");
        passe = DomainValidation.requireRange(passe, 0, 100, "passe");
        marcacao = DomainValidation.requireRange(marcacao, 0, 100, "marcacao");
        potencial = DomainValidation.requireRange(potencial, 0, 100, "potencial");
    }
}
