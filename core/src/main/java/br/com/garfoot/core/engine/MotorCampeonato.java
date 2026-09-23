package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.ClassificacaoItem;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.partida.Partida;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/** Generates and simulates a deterministic double round-robin league season. */
public final class MotorCampeonato {
    private final MotorSimulacaoPartida motorPartida;

    public MotorCampeonato() {
        this(new MotorSimulacaoPartida());
    }

    public MotorCampeonato(MotorSimulacaoPartida motorPartida) {
        this.motorPartida = Objects.requireNonNull(motorPartida, "motorPartida must not be null");
    }

    public List<Rodada> gerarTurnoEReturno(Campeonato campeonato, LocalDateTime inicio) {
        Objects.requireNonNull(campeonato, "campeonato must not be null");
        Objects.requireNonNull(inicio, "inicio must not be null");
        if (campeonato.participantes().size() < 2) {
            throw new IllegalArgumentException("league needs at least two participants");
        }
        if (!campeonato.rodadas().isEmpty()) {
            throw new IllegalStateException("league schedule already exists");
        }

        List<Clube> rotacao = new ArrayList<>(campeonato.participantes());
        if (rotacao.size() % 2 != 0) {
            rotacao.add(null);
        }
        int timesPorTurno = rotacao.size() - 1;
        int partidasPorRodada = rotacao.size() / 2;
        List<Rodada> turno = new ArrayList<>();
        for (int numero = 1; numero <= timesPorTurno; numero++) {
            Rodada rodada = new Rodada(numero);
            for (int indice = 0; indice < partidasPorRodada; indice++) {
                Clube primeiro = rotacao.get(indice);
                Clube segundo = rotacao.get(rotacao.size() - 1 - indice);
                if (primeiro != null && segundo != null) {
                    boolean primeiroManda = (numero + indice) % 2 == 0;
                    Clube mandante = primeiroManda ? primeiro : segundo;
                    Clube visitante = primeiroManda ? segundo : primeiro;
                    rodada.adicionarPartida(new Partida(UUID.randomUUID(), mandante, visitante,
                            inicio.plusDays((long) (numero - 1) * 7)));
                }
            }
            campeonato.adicionarRodada(rodada);
            turno.add(rodada);
            Clube ultimo = rotacao.remove(rotacao.size() - 1);
            rotacao.add(1, ultimo);
        }
        for (Rodada rodadaTurno : turno) {
            Rodada returno = new Rodada(rodadaTurno.numero() + timesPorTurno);
            for (Partida partida : rodadaTurno.partidas()) {
                returno.adicionarPartida(new Partida(UUID.randomUUID(), partida.visitante(), partida.mandante(),
                        partida.dataHora().plusDays((long) timesPorTurno * 7)));
            }
            campeonato.adicionarRodada(returno);
        }
        return campeonato.rodadas();
    }

    public List<ClassificacaoItem> simularTemporada(Campeonato campeonato, long seed) {
        Objects.requireNonNull(campeonato, "campeonato must not be null");
        if (campeonato.rodadas().isEmpty()) {
            throw new IllegalStateException("generate the league schedule before simulating the season");
        }
        Map<UUID, Estatisticas> tabela = new HashMap<>();
        campeonato.participantes().forEach(clube -> tabela.put(clube.id(), new Estatisticas(clube)));
        long indicePartida = 0;
        for (Rodada rodada : campeonato.rodadas()) {
            for (Partida partida : rodada.partidas()) {
                long seedPartida = seed + indicePartida++ * 0x9E3779B97F4A7C15L;
                var taticaMandante = partida.mandante().tatica();
                var taticaVisitante = partida.visitante().tatica();
                ResultadoSimulacao resultado = taticaMandante != null && taticaVisitante != null
                        ? motorPartida.simular(forca(partida.mandante()), forca(partida.visitante()),
                                taticaMandante.escalacao(), taticaVisitante.escalacao(), seedPartida)
                        : motorPartida.simular(forca(partida.mandante()), forca(partida.visitante()),
                                partida.mandante().elenco(), partida.visitante().elenco(), seedPartida);
                resultado.aplicarA(partida);
                tabela.get(partida.mandante().id()).registrar(resultado.golsMandante(), resultado.golsVisitante());
                tabela.get(partida.visitante().id()).registrar(resultado.golsVisitante(), resultado.golsMandante());
            }
        }
        List<ClassificacaoItem> classificacao = tabela.values().stream()
                .map(Estatisticas::item)
                .sorted(Comparator.comparingInt(ClassificacaoItem::pontos).reversed()
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::saldoGols).reversed())
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::golsPro).reversed())
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::vitorias).reversed())
                        .thenComparing(item -> item.clube().nome())
                        .thenComparing(item -> item.clube().id().toString()))
                .toList();
        campeonato.atualizarClassificacao(classificacao);
        return campeonato.classificacao();
    }

    private static ForcaEquipe forca(Clube clube) {
        if (clube.elenco().isEmpty()) {
            return new ForcaEquipe(50, 50);
        }
        return ForcaEquipe.aPartirDosJogadores(clube.tatica() == null ? clube.elenco() : clube.tatica().escalacao().titulares());
    }

    private static final class Estatisticas {
        private final Clube clube;
        private int pontos;
        private int vitorias;
        private int empates;
        private int derrotas;
        private int golsPro;
        private int golsContra;

        private Estatisticas(Clube clube) { this.clube = clube; }

        private void registrar(int feitos, int sofridos) {
            golsPro += feitos;
            golsContra += sofridos;
            if (feitos > sofridos) { vitorias++; pontos += 3; }
            else if (feitos == sofridos) { empates++; pontos++; }
            else { derrotas++; }
        }

        private ClassificacaoItem item() {
            return new ClassificacaoItem(clube, pontos, vitorias, empates, derrotas, golsPro, golsContra);
        }
    }
}
