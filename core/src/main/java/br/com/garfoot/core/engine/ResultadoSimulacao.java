package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.EventoPartida;

import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public record ResultadoSimulacao(int golsMandante, int golsVisitante, List<EventoPartida> eventos) {
    public ResultadoSimulacao {
        if (golsMandante < 0 || golsVisitante < 0) {
            throw new IllegalArgumentException("goals must not be negative");
        }
        eventos = eventos.stream().sorted(Comparator.comparingInt(EventoPartida::minuto)).toList();
        long golsNarrados = eventos.stream().filter(evento -> evento.tipo()
                == br.com.garfoot.core.model.partida.TipoEvento.GOL).count();
        if (golsNarrados != (long) golsMandante + golsVisitante) {
            throw new IllegalArgumentException("goal events must match the simulated score");
        }
    }

    public List<EventoPartida> eventos() {
        return Collections.unmodifiableList(eventos);
    }

    public void aplicarA(Partida partida) {
        partida.aplicarResultado(golsMandante, golsVisitante, eventos);
    }

    public String narracao() {
        return eventos.stream()
                .map(evento -> evento.minuto() + "' " + evento.descricaoNarrativa())
                .reduce((primeiro, segundo) -> primeiro + "\n" + segundo)
                .orElse("A partida terminou sem eventos narrados.");
    }
}
