package br.com.garfoot.core.model.jogador;

import br.com.garfoot.core.util.DomainValidation;

import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

public final class Jogador {
    private final UUID id;
    private final String nome;
    private final LocalDate dataNascimento;
    private final Posicao posicao;
    private final AtributosJogador atributos;
    private int moral;
    private int condicaoFisica;
    private StatusJogador status;

    public Jogador(
            UUID id,
            String nome,
            LocalDate dataNascimento,
            Posicao posicao,
            AtributosJogador atributos) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.nome = DomainValidation.requireText(nome, "nome");
        this.dataNascimento = Objects.requireNonNull(dataNascimento, "dataNascimento must not be null");
        this.posicao = Objects.requireNonNull(posicao, "posicao must not be null");
        this.atributos = Objects.requireNonNull(atributos, "atributos must not be null");
        this.moral = 50;
        this.condicaoFisica = 100;
        this.status = StatusJogador.DISPONIVEL;
    }

    public UUID id() {
        return id;
    }

    public String nome() {
        return nome;
    }

    public LocalDate dataNascimento() {
        return dataNascimento;
    }

    public Posicao posicao() {
        return posicao;
    }

    public AtributosJogador atributos() {
        return atributos;
    }

    public int moral() {
        return moral;
    }

    public int condicaoFisica() {
        return condicaoFisica;
    }

    public StatusJogador status() {
        return status;
    }

    public void atualizarMoral(int valor) {
        moral = DomainValidation.requireRange(valor, 0, 100, "moral");
    }

    public void atualizarCondicaoFisica(int valor) {
        condicaoFisica = DomainValidation.requireRange(valor, 0, 100, "condicaoFisica");
    }

    public void atualizarStatus(StatusJogador novoStatus) {
        status = Objects.requireNonNull(novoStatus, "novoStatus must not be null");
    }
}
