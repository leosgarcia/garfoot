package br.com.garfoot.core.model.campeonato;

import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.util.DomainValidation;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

public final class Campeonato {
    private final UUID id;
    private final String nome;
    private final TipoCompeticao tipo;
    private final List<Clube> participantes = new ArrayList<>();
    private final List<Rodada> rodadas = new ArrayList<>();
    private final List<ClassificacaoItem> classificacao = new ArrayList<>();

    public Campeonato(UUID id, String nome, TipoCompeticao tipo) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.nome = DomainValidation.requireText(nome, "nome");
        this.tipo = Objects.requireNonNull(tipo, "tipo must not be null");
    }

    public UUID id() {
        return id;
    }

    public String nome() {
        return nome;
    }

    public TipoCompeticao tipo() {
        return tipo;
    }

    public List<Clube> participantes() {
        return Collections.unmodifiableList(participantes);
    }

    public List<Rodada> rodadas() {
        return Collections.unmodifiableList(rodadas);
    }

    public List<ClassificacaoItem> classificacao() {
        return Collections.unmodifiableList(classificacao);
    }

    public void atualizarClassificacao(List<ClassificacaoItem> novaClassificacao) {
        Objects.requireNonNull(novaClassificacao, "novaClassificacao must not be null");
        if (novaClassificacao.size() != participantes.size()
                || novaClassificacao.stream().map(item -> item.clube().id()).distinct().count() != participantes.size()
                || novaClassificacao.stream().anyMatch(item -> participantes.stream()
                .noneMatch(clube -> clube.id().equals(item.clube().id())))) {
            throw new IllegalArgumentException("classification must contain every participant exactly once");
        }
        classificacao.clear();
        classificacao.addAll(novaClassificacao);
    }

    public void adicionarParticipante(Clube clube) {
        Objects.requireNonNull(clube, "clube must not be null");
        if (participantes.stream().anyMatch(item -> item.id().equals(clube.id()))) {
            throw new IllegalArgumentException("club already participates");
        }
        participantes.add(clube);
    }

    public void adicionarRodada(Rodada rodada) {
        Objects.requireNonNull(rodada, "rodada must not be null");
        if (rodadas.stream().anyMatch(item -> item.numero() == rodada.numero())) {
            throw new IllegalArgumentException("round number already exists");
        }
        rodadas.add(rodada);
    }
}
