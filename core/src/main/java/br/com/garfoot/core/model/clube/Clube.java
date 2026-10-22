package br.com.garfoot.core.model.clube;

import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.tatica.Tatica;
import br.com.garfoot.core.util.DomainValidation;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

public final class Clube {
    private final UUID id;
    private final String nome;
    private final String sigla;
    private final List<Jogador> elenco = new ArrayList<>();
    private Tecnico tecnico;
    private Tatica tatica;
    private long valorElencoEur;
    private String pais = "Brasil";
    private boolean elencoSintetico;
    private boolean elencoCompletadoSinteticamente;

    public Clube(UUID id, String nome, String sigla) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.nome = DomainValidation.requireText(nome, "nome");
        this.sigla = DomainValidation.requireText(sigla, "sigla");
    }

    public UUID id() {
        return id;
    }

    public String nome() {
        return nome;
    }

    public String sigla() {
        return sigla;
    }

    public List<Jogador> elenco() {
        return Collections.unmodifiableList(elenco);
    }

    public Tecnico tecnico() {
        return tecnico;
    }

    public void definirTecnico(Tecnico tecnico) {
        this.tecnico = Objects.requireNonNull(tecnico, "tecnico must not be null");
    }

    public Tatica tatica() { return tatica; }
    public long valorElencoEur() { return valorElencoEur; }
    public String pais() { return pais; }
    public void definirPais(String pais) { this.pais = DomainValidation.requireText(pais, "pais"); }
    public boolean elencoSintetico() { return elencoSintetico; }
    public void definirElencoSintetico(boolean sintetico) { elencoSintetico = sintetico; }
    public boolean elencoCompletadoSinteticamente() { return elencoCompletadoSinteticamente; }
    public void definirElencoCompletadoSinteticamente(boolean complementado) { elencoCompletadoSinteticamente = complementado; }
    public void definirValorElencoEur(long valor) {
        if (valor < 0) throw new IllegalArgumentException("valorElencoEur must not be negative");
        valorElencoEur = valor;
    }

    public void definirTatica(Tatica tatica) {
        Objects.requireNonNull(tatica, "tatica must not be null");
        if (java.util.stream.Stream.concat(tatica.escalacao().titulares().stream(),
                tatica.escalacao().reservas().stream()).anyMatch(j -> elenco.stream().noneMatch(item -> item.id().equals(j.id())))) {
            throw new IllegalArgumentException("all tactical players must belong to the club");
        }
        this.tatica = tatica;
    }

    public void adicionarJogador(Jogador jogador) {
        Objects.requireNonNull(jogador, "jogador must not be null");
        if (elenco.stream().anyMatch(item -> item.id().equals(jogador.id()))) {
            throw new IllegalArgumentException("jogador already belongs to the club");
        }
        elenco.add(jogador);
    }
}
