package br.com.garfoot.core.model.partida;

import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.util.DomainValidation;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

public final class Partida {
    private final UUID id;
    private final Clube mandante;
    private final Clube visitante;
    private final LocalDateTime dataHora;
    private final List<EventoPartida> eventos = new ArrayList<>();
    private int golsMandante;
    private int golsVisitante;
    private StatusPartida status = StatusPartida.AGENDADA;

    public Partida(UUID id, Clube mandante, Clube visitante, LocalDateTime dataHora) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.mandante = Objects.requireNonNull(mandante, "mandante must not be null");
        this.visitante = Objects.requireNonNull(visitante, "visitante must not be null");
        if (mandante.id().equals(visitante.id())) {
            throw new IllegalArgumentException("mandante and visitante must be different clubs");
        }
        this.dataHora = Objects.requireNonNull(dataHora, "dataHora must not be null");
    }

    public UUID id() {
        return id;
    }

    public Clube mandante() {
        return mandante;
    }

    public Clube visitante() {
        return visitante;
    }

    public LocalDateTime dataHora() {
        return dataHora;
    }

    public int golsMandante() {
        return golsMandante;
    }

    public int golsVisitante() {
        return golsVisitante;
    }

    public StatusPartida status() {
        return status;
    }

    public List<EventoPartida> eventos() {
        return Collections.unmodifiableList(eventos);
    }

    public void iniciar() {
        if (status != StatusPartida.AGENDADA) {
            throw new IllegalStateException("only scheduled matches can start");
        }
        status = StatusPartida.EM_ANDAMENTO;
    }

    public void registrarGolMandante() {
        exigirEmAndamento();
        golsMandante++;
    }

    public void registrarGolVisitante() {
        exigirEmAndamento();
        golsVisitante++;
    }

    public void registrarEvento(EventoPartida evento) {
        exigirEmAndamento();
        Objects.requireNonNull(evento, "evento must not be null");
        eventos.add(evento);
    }

    public void aplicarResultado(int golsMandante, int golsVisitante, List<EventoPartida> eventosSimulados) {
        if (status != StatusPartida.AGENDADA) {
            throw new IllegalStateException("only scheduled matches can receive a simulation result");
        }
        if (golsMandante < 0 || golsVisitante < 0) {
            throw new IllegalArgumentException("goals must not be negative");
        }
        Objects.requireNonNull(eventosSimulados, "eventosSimulados must not be null");
        List<EventoPartida> copiaEventos = List.copyOf(eventosSimulados);
        iniciar();
        this.golsMandante = golsMandante;
        this.golsVisitante = golsVisitante;
        eventos.addAll(copiaEventos);
        encerrar();
    }

    public void encerrar() {
        if (status != StatusPartida.EM_ANDAMENTO) {
            throw new IllegalStateException("only ongoing matches can finish");
        }
        status = StatusPartida.ENCERRADA;
    }

    private void exigirEmAndamento() {
        if (status != StatusPartida.EM_ANDAMENTO) {
            throw new IllegalStateException("match must be ongoing");
        }
    }
}
